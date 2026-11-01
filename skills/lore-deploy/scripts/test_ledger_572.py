"""Contract (#572): the host ``<slug>.db`` is lore-deploy's LEDGER, never an index.

Ruling: ``docs/plans/v2/receipts/2026-10-31-165/RULING-572-ledger.md`` (operator, 2026-10-31).
Since P5 no loremaster code writes the host SQLite ``<slug>.db``; the index lives in the store
(``SurrealManifest``). The file is now the deploy script's ledger:

* it holds the owning ``project_path`` plus a PROVISIONED MARKER, written only by ``setup``,
  and the marker only after a SUCCESSFUL cold index;
* ``setup``'s "already provisioned" decision reads the marker; index state is never inferred
  from the ledger (neither from the file existing, nor from an owner row, nor from a legacy
  pre-P5 ``files`` table);
* ``status`` never shows a file or chunk count from the ledger, says the index counts live in
  the store, and names ``lore_index()`` as where to read them; the owner path and the marker
  are shown as what they are.

The marker's spelling is the builder's choice: every pin here observes it through behaviour
(what a second ``setup`` does, what ``status`` prints), never by reading a key.

Run from this directory::

    uv run python -m pytest test_ledger_572.py -q
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import lore_deploy
import pytest
from config_reader_fake import realistic_config_document, write_config_document

# ---------------------------------------------------------------------------
# Fixture data.
# ---------------------------------------------------------------------------
#: A real hyphenated repo name and its slug (the #568 headline), plus a second live
#: deployment's slug, so no pin is satisfied by one slug value only.
PROJECT_NAME_TO_SLUG: dict[str, str] = {
    "odoo-custom": "odoo_custom",
    "demand_intelligence": "demand_intelligence",
}
#: A HOSTILE project directory name: a newline, then a line shaped exactly like status's own
#: output claiming an index fact. Linux permits it; the slug comes from the lore.yaml.
FORGED_STATUS_LINE = "status: index = 2917 files, 20419 chunks (provisioned)"
HOSTILE_PROJECT_NAME = f"odoo-custom\n{FORGED_STATUS_LINE}"
PROJECT_NAME_TO_SLUG[HOSTILE_PROJECT_NAME] = "odoo_custom"

#: The legacy pre-P5 ledger schema, measured 2026-10-31 with ``sqlite3 <file> .schema`` (schema
#: only, no row data) on ``~/.local/state/lore/lore.db`` and ``demand_intelligence.db``.
LEGACY_FILES_DDL = """CREATE TABLE files (
    tier       TEXT NOT NULL,
    file_path  TEXT NOT NULL,
    sha512     TEXT NOT NULL,
    mtime_ns   INTEGER NOT NULL,
    size       INTEGER NOT NULL,
    n_chunks   INTEGER NOT NULL,
    chunk_ids  TEXT NOT NULL,
    state      TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (tier, file_path)
)"""
LEGACY_META_DDL = """CREATE TABLE IF NOT EXISTS meta (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
)"""
#: The ``meta`` keys a pre-P5 index wrote (key names as the #568 contract recorded them).
LEGACY_META: dict[str, str] = {
    "embedding_schema_fingerprint": "f" * 64,
    "schema_rebuild_status": '{"state": "done"}',
}

#: Two legacy ``files`` populations with deliberately unrelated counts. A repo of this size
#: indexes a few hundred to a few thousand files; per-file chunk counts of 3 and 7 give chunk
#: totals (1236, 20419) that a status line counting either column would print.
LEGACY_POPULATIONS: dict[str, tuple[int, int]] = {
    "small": (412, 3),
    "large": (2917, 7),
}
#: Legacy row states, mixed so a per-state rollup (``indexed=…``, ``failed=…``) has two keys.
LEGACY_STATES: tuple[str, ...] = ("indexed", "indexed", "indexed", "failed")

#: The cold-index exit codes the stub returns: success, and the indexer's failure exit.
INDEX_SUCCEEDS = 0
INDEX_FAILS = 1

#: The pointer the ruling names for where the index counts live.
INDEX_COUNTS_POINTER = "lore_index"
#: The line HEAD prints when it cannot read a ``files`` table from a meta-only ledger.
UNREADABLE_TOKEN = "unreadable"

#: podman verbs a setup or status may issue that create, change or remove a container.
PODMAN_MUTATING_VERBS = frozenset({"run", "start", "stop", "rm", "kill", "restart", "create"})


# ---------------------------------------------------------------------------
# Hermetic environment.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _hermetic_deploy_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point every host-global path at ``tmp_path``; give the config loader dummy secrets.

    ``_loremaster_python`` is the test interpreter, so the slug resolver, config reads and the
    ``.mcp.json`` merge run for REAL. No test reads or writes the host's real ledgers.
    """
    monkeypatch.setattr(lore_deploy, "_loremaster_python", lambda: sys.executable)
    monkeypatch.setattr(lore_deploy, "MANIFEST_DIR", tmp_path / "state")
    monkeypatch.setattr(lore_deploy, "LORE_SECRETS_DIR", tmp_path / "lore-secrets")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic-key")
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "root")
    monkeypatch.setenv("LORE_TEI_KEY", "dummy-tei-key")


@dataclass
class DeployShim:
    """Stands in for podman and the cold index at the ``_run`` seam; runs everything else.

    * podman: no container exists (``inspect`` exits 125, as podman does), the image exists,
      and any other podman call raises so an unmodelled query fails loudly.
    * The cold index (``-m loremaster.index``) is recorded and exits ``index_returncode``. Like
      the real indexer since P5, it writes NOTHING to the host ledger: the index lives in the
      store, so whatever ``<slug>.db`` holds afterwards, ``setup`` wrote.
    * Everything else (config reads, the slug normaliser, ``merge_mcp_json.py``) runs for real.
    """

    real_run: Callable[..., subprocess.CompletedProcess[str]]
    index_returncode: int = INDEX_SUCCEEDS
    index_calls: list[list[str]] = field(default_factory=list)
    podman_calls: list[list[str]] = field(default_factory=list)

    def __call__(
        self, cmd: list[str], *, check: bool = True, capture: bool = False
    ) -> subprocess.CompletedProcess[str]:
        """Answer podman / the cold index; delegate everything else to the real ``_run``."""
        if cmd and cmd[0] == "podman":
            self.podman_calls.append(list(cmd))
            if cmd[1:3] == ["container", "inspect"]:
                return subprocess.CompletedProcess(cmd, 125, stdout="", stderr="no such container")
            if cmd[1:3] == ["image", "exists"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            raise AssertionError(f"DeployShim does not model {cmd!r}; extend it")
        if "loremaster.index" in cmd:
            self.index_calls.append(list(cmd))
            stderr = "" if self.index_returncode == INDEX_SUCCEEDS else "embedder 503: 17 files failed"
            return subprocess.CompletedProcess(cmd, self.index_returncode, stdout="", stderr=stderr)
        return self.real_run(cmd, check=check, capture=capture)

    @classmethod
    def install(cls, monkeypatch: pytest.MonkeyPatch, *, index_returncode: int) -> DeployShim:
        """Install the shim over ``lore_deploy._run``."""
        shim = cls(real_run=lore_deploy._run, index_returncode=index_returncode)
        monkeypatch.setattr(lore_deploy, "_run", shim)
        return shim


def _stub_probes(monkeypatch: pytest.MonkeyPatch, *, result: int) -> None:
    """Arrange the embed and store probes to return ``result``; neither touches a network.

    A FAILING probe is how a pin makes "setup fell through its provisioned check" visible: a
    provisioned project never reaches the probes.
    """
    probe = lambda *args, **kwargs: result  # noqa: E731 - a one-line stub
    monkeypatch.setattr(lore_deploy, "_probe_embed", probe)
    monkeypatch.setattr(lore_deploy, "_probe_surreal", probe)


# ---------------------------------------------------------------------------
# Scene: one project, its config, its secrets file, and its ledger.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OutcomeOfVerb:
    """What one verb call did: its exit code or raise, and its streams."""

    return_code: int | None
    raised: BaseException | None
    stdout: str
    stderr: str


@dataclass
class LedgerScene:
    """A configured project whose ledger the test arranges through the production writers."""

    project: Path
    slug: str
    env_file: Path
    capsys: pytest.CaptureFixture[str]
    monkeypatch: pytest.MonkeyPatch

    @classmethod
    def build(
        cls,
        tmp_path: Path,
        name: str,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> LedgerScene:
        """A project dir named ``name`` with a production-shaped lore.yaml and a secrets file."""
        slug = PROJECT_NAME_TO_SLUG[name]
        project = tmp_path / "projects" / name
        project.mkdir(parents=True)
        write_config_document(realistic_config_document(slug=slug), project / lore_deploy.CONFIG_FILENAME)
        env_file = tmp_path / "secrets.env"
        env_file.write_text("LORE_TEI_KEY=dummy-tei-key\n", encoding="utf-8")
        return cls(project, slug, env_file, capsys, monkeypatch)

    @property
    def tmp_root(self) -> Path:
        """The hermetic root every path in this scene lives under."""
        return lore_deploy.MANIFEST_DIR.parent

    @property
    def ledger(self) -> Path:
        """The host ledger file for this slug."""
        return lore_deploy.MANIFEST_DIR / f"{self.slug}.db"

    # -- ledger arrangements (each through the writer production uses, or the measured shape)
    def record_owner_only(self) -> None:
        """An owner row and no marker: what the #568 backfill (``ManifestOwner.record``) leaves."""
        lore_deploy.ManifestOwner(self.slug).record(self.project)

    def write_legacy_ledger(self, population: str) -> None:
        """A pre-P5 ledger: the measured schema, legacy meta, ``files`` rows, NO owner row."""
        lore_deploy.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.ledger) as connection:
            connection.execute(LEGACY_META_DDL)
            connection.executemany("INSERT OR REPLACE INTO meta VALUES (?, ?)", LEGACY_META.items())
        self.replace_files_table(population)

    def replace_files_table(self, population: str | None) -> None:
        """Drop any ``files`` table; recreate it holding ``population`` (``"empty"`` = no rows).

        ``None`` leaves the ledger with no ``files`` table at all (a meta-only ledger).
        """
        with sqlite3.connect(self.ledger) as connection:
            connection.execute("DROP TABLE IF EXISTS files")
            if population is None:
                return
            connection.execute(LEGACY_FILES_DDL)
            if population == "empty":
                return
            file_count, chunks_per_file = LEGACY_POPULATIONS[population]
            connection.executemany(
                "INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        "custom",
                        f"loremaster/loremaster/module_{index:04d}.py",
                        f"{index:0128x}",
                        1_761_868_800_000_000_000 + index,
                        4_096 + index,
                        chunks_per_file,
                        "[]",
                        LEGACY_STATES[index % len(LEGACY_STATES)],
                        "2026-07-03T14:12:09Z",
                    )
                    for index in range(file_count)
                ],
            )

    def provision(self) -> OutcomeOfVerb:
        """Provision through the REAL ``setup`` with probes passing and the cold index succeeding."""
        _stub_probes(self.monkeypatch, result=lore_deploy._EXIT_OK)
        shim = DeployShim.install(self.monkeypatch, index_returncode=INDEX_SUCCEEDS)
        outcome = self.setup()
        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
            f"arranging a provisioned {self.slug} ledger: setup must succeed when the cold index "
            f"succeeds; rc={outcome.return_code} raised={outcome.raised!r} stderr={outcome.stderr!r}"
        )
        assert len(shim.index_calls) == 1, f"arranging: setup must cold-index once; ran {shim.index_calls}"
        return outcome

    # -- verbs
    def _drive(self, call: Callable[[], int]) -> OutcomeOfVerb:
        self.capsys.readouterr()  # discard anything an arrangement printed
        return_code: int | None = None
        raised: BaseException | None = None
        try:
            return_code = call()
        except Exception as error:  # noqa: BLE001 - a raise is an outcome to classify
            raised = error
        captured = self.capsys.readouterr()
        return OutcomeOfVerb(return_code, raised, captured.out, captured.err)

    def setup(self, env_file: Path | None = None) -> OutcomeOfVerb:
        """Run the real ``verb_setup`` (``env_file`` defaults to the scene's secrets file)."""
        chosen = self.env_file if env_file is None else env_file
        return self._drive(lambda: lore_deploy.verb_setup(self.project, chosen))

    def status(self) -> OutcomeOfVerb:
        """Run the real ``verb_status`` against an absent container."""
        DeployShim.install(self.monkeypatch, index_returncode=INDEX_SUCCEEDS)
        return self._drive(lambda: lore_deploy.verb_status(self.project))

    def setup_reindexes(self) -> tuple[OutcomeOfVerb, DeployShim]:
        """Re-run setup with everything a FRESH provision needs; return what it did."""
        _stub_probes(self.monkeypatch, result=lore_deploy._EXIT_OK)
        shim = DeployShim.install(self.monkeypatch, index_returncode=INDEX_SUCCEEDS)
        return self.setup(), shim

    def setup_short_circuits(self) -> tuple[OutcomeOfVerb, DeployShim]:
        """Re-run setup where ANY fall-through past the provisioned check fails loudly.

        The secrets file is absent and both probes fail, so only a setup that decided "already
        provisioned" can return ``_EXIT_OK``; and the cold index, if reached, is recorded.
        """
        _stub_probes(self.monkeypatch, result=lore_deploy._EXIT_ERROR)
        shim = DeployShim.install(self.monkeypatch, index_returncode=INDEX_SUCCEEDS)
        return self.setup(env_file=self.project.parent / "absent.env"), shim


def _assert_ok(outcome: OutcomeOfVerb, what: str) -> None:
    assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
        f"{what}: rc={outcome.return_code} raised={outcome.raised!r} stderr={outcome.stderr!r}"
    )


@pytest.fixture(params=sorted(name for name in PROJECT_NAME_TO_SLUG if name != HOSTILE_PROJECT_NAME))
def scene(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> LedgerScene:
    """A configured project, once per realistic project name."""
    return LedgerScene.build(tmp_path, request.param, capsys, monkeypatch)


# ---------------------------------------------------------------------------
# 1. The marker is written only after a SUCCESSFUL cold index.
# ---------------------------------------------------------------------------
class TestSetupMarksProvisionedOnlyAfterASuccessfulColdIndex:
    """``setup`` writes the provisioned marker iff its cold index succeeded."""

    def test_a_project_setup_provisioned_is_recognised_on_the_next_setup(
        self, scene: LedgerScene
    ) -> None:
        """Successful index → the next setup is a no-op: no re-index, no probe, no secrets needed."""
        scene.provision()

        outcome, shim = scene.setup_short_circuits()

        _assert_ok(outcome, "a project setup provisioned must be recognised as provisioned")
        assert shim.index_calls == [], (
            f"a provisioned project must not be re-indexed; ran {shim.index_calls}"
        )
        assert [cmd for cmd in shim.podman_calls if cmd[1] in PODMAN_MUTATING_VERBS] == [], (
            "re-running setup on a provisioned project must touch no container"
        )

    def test_a_failed_cold_index_leaves_the_project_unprovisioned(
        self, scene: LedgerScene
    ) -> None:
        """Failed index → setup fails, and the NEXT setup cold-indexes again.

        A marker written before the index (or written regardless of its exit) makes the next
        setup a no-op over an index that never completed.
        """
        _stub_probes(scene.monkeypatch, result=lore_deploy._EXIT_OK)
        failing = DeployShim.install(scene.monkeypatch, index_returncode=INDEX_FAILS)
        failed = scene.setup()
        assert failed.raised is None and failed.return_code == lore_deploy._EXIT_ERROR, (
            f"a failed cold index must fail setup; rc={failed.return_code} raised={failed.raised!r}"
        )
        assert len(failing.index_calls) == 1, (
            f"setup must have tried the cold index; ran {failing.index_calls}"
        )

        retried, shim = scene.setup_reindexes()

        _assert_ok(retried, "the setup after a failed cold index must provision")
        assert len(shim.index_calls) == 1, (
            f"after a FAILED cold index the next setup must cold-index again; ran {shim.index_calls}"
        )

    def test_a_failed_cold_index_over_an_owner_only_ledger_leaves_it_unprovisioned(
        self, scene: LedgerScene
    ) -> None:
        """Owner row present, index fails → still unprovisioned: the next setup indexes."""
        scene.record_owner_only()
        _stub_probes(scene.monkeypatch, result=lore_deploy._EXIT_OK)
        DeployShim.install(scene.monkeypatch, index_returncode=INDEX_FAILS)
        failed = scene.setup()
        assert failed.return_code == lore_deploy._EXIT_ERROR, (
            f"a failed cold index must fail setup; rc={failed.return_code} raised={failed.raised!r} "
            f"stderr={failed.stderr!r}"
        )

        retried, shim = scene.setup_reindexes()

        _assert_ok(retried, "the setup after a failed cold index must provision")
        assert len(shim.index_calls) == 1, (
            f"after a FAILED cold index the next setup must cold-index again; ran {shim.index_calls}"
        )


# ---------------------------------------------------------------------------
# 2. "Already provisioned" follows the marker, never the file, the owner row or legacy rows.
# ---------------------------------------------------------------------------
class TestProvisionedDecisionFollowsTheMarker:
    """Index state is never inferred from the ledger: only the marker says "provisioned"."""

    def test_an_owner_only_ledger_is_not_provisioned(self, scene: LedgerScene) -> None:
        """Owner row, no marker (the #568 backfill's shape) → setup cold-indexes once, then is done."""
        scene.record_owner_only()

        outcome, shim = scene.setup_reindexes()

        _assert_ok(outcome, "setup over an owner-only ledger must provision, not refuse")
        assert len(shim.index_calls) == 1, (
            f"an owner row is not a provisioned marker: setup must cold-index; ran {shim.index_calls}"
        )
        again, shim_again = scene.setup_short_circuits()
        _assert_ok(again, "after that cold index the project must be provisioned")
        assert shim_again.index_calls == [], f"it must not be re-indexed; ran {shim_again.index_calls}"

    def test_an_owner_only_ledger_is_never_a_no_op(self, scene: LedgerScene) -> None:
        """Owner row, no marker, no secrets → setup reaches the work and FAILS, never a no-op.

        A build whose "provisioned" means "the ledger file exists" (or "an owner is recorded")
        returns ``_EXIT_OK`` here having indexed nothing.
        """
        scene.record_owner_only()

        outcome, shim = scene.setup_short_circuits()

        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_ERROR, (
            f"an owner-only ledger is not provisioned: setup must not report a no-op success; "
            f"rc={outcome.return_code} stdout={outcome.stdout!r}"
        )

    @pytest.mark.parametrize("population", sorted(LEGACY_POPULATIONS))
    def test_a_legacy_ledger_with_indexed_files_is_not_provisioned(
        self, scene: LedgerScene, population: str
    ) -> None:
        """A pre-P5 ledger (``files`` rows, no owner, no marker) + its lore.yaml → setup indexes.

        The live ledgers on this host have this shape (schema measured 2026-10-31). Their
        ``files`` rows describe an index nothing has written since P5, so they prove nothing.
        The setup still is not refused (the project's own lore.yaml claims the slug).
        """
        scene.write_legacy_ledger(population)

        outcome, shim = scene.setup_reindexes()

        _assert_ok(outcome, "setup over this project's own legacy ledger must provision, not refuse")
        assert len(shim.index_calls) == 1, (
            f"legacy files rows are not a provisioned marker: setup must cold-index; ran {shim.index_calls}"
        )
        again, shim_again = scene.setup_short_circuits()
        _assert_ok(again, "after that cold index the project must be provisioned")
        assert shim_again.index_calls == [], f"it must not be re-indexed; ran {shim_again.index_calls}"

    def test_the_cold_index_runs_against_this_projects_config(self, scene: LedgerScene) -> None:
        """The index setup runs for an unprovisioned ledger is THIS project's lore.yaml."""
        scene.record_owner_only()

        _, shim = scene.setup_reindexes()

        config_path = str(scene.project / lore_deploy.CONFIG_FILENAME)
        assert len(shim.index_calls) == 1 and config_path in shim.index_calls[0], (
            f"setup must cold-index {config_path}; ran {shim.index_calls}"
        )

    def test_status_does_not_provision_an_owner_only_ledger(self, scene: LedgerScene) -> None:
        """The marker is written only by setup: a status run leaves an owner-only ledger unprovisioned."""
        scene.record_owner_only()
        _assert_ok(scene.status(), "status over an owner-only ledger")

        _, shim = scene.setup_reindexes()

        assert len(shim.index_calls) == 1, (
            f"status must not mark the project provisioned; the next setup ran {shim.index_calls}"
        )


# ---------------------------------------------------------------------------
# 3. ``status`` reports the ledger as a ledger: no counts from it, a pointer to the store.
# ---------------------------------------------------------------------------
#: How each base ledger state is arranged on a scene.
def _arrange_provisioned(scene: LedgerScene) -> None:
    """Owner + marker, written by the real ``setup`` after a successful cold index."""
    scene.provision()


def _arrange_legacy(scene: LedgerScene) -> None:
    """The pre-P5 ledger shape (``files`` rows, legacy meta, no owner, no marker)."""
    scene.write_legacy_ledger("small")


LEDGER_STATES: dict[str, Callable[[LedgerScene], None]] = {
    "owner_only": LedgerScene.record_owner_only,
    "owner_and_marker": _arrange_provisioned,
    "legacy_pre_p5": _arrange_legacy,
}
#: The ``files``-table variants every ledger state is re-rendered under: none, empty, two sizes.
FILES_TABLE_VARIANTS: tuple[str | None, ...] = (None, "empty", "small", "large")


class TestStatusShowsNoIndexFactFromTheLedger:
    """``status`` never derives a file or chunk count from the ledger, and points at the store."""

    @pytest.mark.parametrize("state", sorted(LEDGER_STATES))
    def test_status_output_does_not_depend_on_the_ledgers_files_table(
        self, scene: LedgerScene, state: str
    ) -> None:
        """Same ledger, ``files`` table absent / empty / 412 rows / 2917 rows → byte-identical status.

        Whatever wording a build picks, a status that counts the table (per state, in total, in
        chunks, or "no files indexed yet" for an empty one), or that reports the table missing
        ("unreadable"), prints different bytes for at least two of these variants.
        """
        LEDGER_STATES[state](scene)
        renders: dict[str | None, OutcomeOfVerb] = {}
        for variant in FILES_TABLE_VARIANTS:
            scene.replace_files_table(variant)
            renders[variant] = scene.status()

        for variant, outcome in renders.items():
            _assert_ok(outcome, f"status over a {state} ledger with files={variant}")
        baseline = renders[FILES_TABLE_VARIANTS[0]]
        differing = {
            variant: (outcome.stdout, outcome.stderr)
            for variant, outcome in renders.items()
            if (outcome.stdout, outcome.stderr) != (baseline.stdout, baseline.stderr)
        }
        assert differing == {}, (
            f"status over a {state} ledger must not read its files table (the index lives in the "
            f"store); output changed with the table: baseline={baseline.stdout!r} vs {differing!r}"
        )

    @pytest.mark.parametrize("state", sorted(LEDGER_STATES))
    def test_status_prints_no_count_of_the_legacy_files_rows(
        self, scene: LedgerScene, state: str
    ) -> None:
        """The 2917-file / 20419-chunk legacy population's counts appear nowhere in status."""
        LEDGER_STATES[state](scene)
        scene.replace_files_table("large")
        file_count, chunks_per_file = LEGACY_POPULATIONS["large"]
        indexed_rows = sum(
            1 for index in range(file_count) if LEGACY_STATES[index % len(LEGACY_STATES)] == "indexed"
        )
        counts = {file_count, file_count * chunks_per_file, indexed_rows, file_count - indexed_rows}

        outcome = scene.status()

        _assert_ok(outcome, f"status over a {state} ledger")
        # Scrub the hermetic tmp paths first: pytest numbers its tmp dirs, and a dir number that
        # happens to equal a count is not a count.
        printed = (outcome.stdout + outcome.stderr).replace(str(scene.tmp_root), "<tmp>")
        leaked = sorted(count for count in counts if str(count) in printed)
        assert leaked == [], (
            f"status must print no file or chunk count from the ledger; found {leaked} in {printed!r}"
        )

    @pytest.mark.parametrize("state", [None, *sorted(LEDGER_STATES)])
    def test_status_names_where_the_index_counts_live(
        self, scene: LedgerScene, state: str | None
    ) -> None:
        """Every ledger state, absent included: status names ``lore_index()`` for the index counts."""
        if state is not None:
            LEDGER_STATES[state](scene)

        outcome = scene.status()

        _assert_ok(outcome, f"status over ledger state {state}")
        assert INDEX_COUNTS_POINTER in outcome.stdout, (
            f"status must say the index counts live in the store and name {INDEX_COUNTS_POINTER}() "
            f"as where to read them; stdout: {outcome.stdout!r}"
        )

    @pytest.mark.parametrize("state", [None, "owner_only", "owner_and_marker"])
    def test_status_over_a_meta_only_ledger_reports_nothing_unreadable(
        self, scene: LedgerScene, state: str | None
    ) -> None:
        """A ledger with no ``files`` table (or none at all) is not an error to report."""
        if state is not None:
            LEDGER_STATES[state](scene)
            scene.replace_files_table(None)

        outcome = scene.status()

        _assert_ok(outcome, f"status over ledger state {state}")
        printed = outcome.stdout + outcome.stderr
        assert UNREADABLE_TOKEN not in printed.lower(), (
            f"a meta-only ledger is the ledger's normal shape, not an unreadable index; got {printed!r}"
        )


class TestStatusShowsTheLedgerAsWhatItIs:
    """The owner path and the provisioned marker are shown; the two states are told apart."""

    @pytest.mark.parametrize("state", ["owner_only", "owner_and_marker"])
    def test_status_shows_the_recorded_owner_path(self, scene: LedgerScene, state: str) -> None:
        """The ledger's recorded ``project_path`` appears in status."""
        LEDGER_STATES[state](scene)

        outcome = scene.status()

        _assert_ok(outcome, f"status over a {state} ledger")
        owner = lore_deploy.ManifestOwner(scene.slug).recorded_path()
        assert owner is not None, f"arranging: the {state} ledger must record an owner"
        assert owner in outcome.stdout, (
            f"status must show the ledger's owner path {owner}; stdout: {outcome.stdout!r}"
        )

    def test_status_tells_provisioned_from_owner_only(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The same project, owner-only then provisioned: status prints different reports.

        Both renders are of ONE project path, so the difference can only be the marker.
        """
        scene = LedgerScene.build(tmp_path, "odoo-custom", capsys, monkeypatch)
        scene.record_owner_only()
        owner_only = scene.status()
        scene.provision()
        provisioned = scene.status()

        _assert_ok(owner_only, "status over the owner-only ledger")
        _assert_ok(provisioned, "status over the provisioned ledger")
        assert owner_only.stdout != provisioned.stdout, (
            f"status must show the provisioned marker: an owner-only ledger and a provisioned one "
            f"printed the same report {provisioned.stdout!r}"
        )

    @pytest.mark.parametrize("state", ["owner_only", "owner_and_marker"])
    def test_a_hostile_owner_path_cannot_forge_a_status_line(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
        state: str,
    ) -> None:
        """An owner path holding a newline + a status-shaped line renders as ONE value, never two lines.

        The owner path is stored text from the ledger, rendered to an agent; a raw render lets
        the directory name print an index claim status never measured.
        """
        scene = LedgerScene.build(tmp_path, HOSTILE_PROJECT_NAME, capsys, monkeypatch)
        LEDGER_STATES[state](scene)

        outcome = scene.status()

        _assert_ok(outcome, f"status over a {state} ledger with a hostile owner path")
        lines = (outcome.stdout + outcome.stderr).splitlines()
        assert FORGED_STATUS_LINE not in [line.strip() for line in lines], (
            f"the owner path's newline let a forged line through as its own status line: {lines!r}"
        )


class TestStatusOverACorruptLedger:
    """C1's class, on the ledger's other reader: a corrupt ledger is reported, never a traceback."""

    def test_status_names_a_corrupt_ledger_without_a_traceback(self, scene: LedgerScene) -> None:
        """Text over ``<slug>.db`` → status does not raise, prints no traceback, names the file.

        The exit code is spec-silent (status is a report); only the honesty of the render is pinned.
        """
        lore_deploy.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
        scene.ledger.write_bytes(b"status: lore-odoo_custom container = absent\n" * 40)

        outcome = scene.status()

        assert outcome.raised is None, (
            f"status must not raise over a corrupt ledger; raised {outcome.raised!r}"
        )
        printed = outcome.stdout + outcome.stderr
        assert "Traceback (most recent call last)" not in printed
        assert str(scene.ledger) in printed, (
            f"status must name the corrupt ledger {scene.ledger}; got {printed!r}"
        )
