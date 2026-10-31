"""Contract (#568): every directory with a valid slug scaffolds, and every verb agrees on it.

``loremaster.config.SLUG_PATTERN`` (``^[a-z0-9][a-z0-9_]*$``) constrains ``project.slug``.
Before this contract, ``lore-deploy setup`` seeded the slug from the project directory name
VERBATIM, so any repo whose directory carries a hyphen or a capital (``odoo-custom``,
``transcribe-craig``, ``PP-Odoo``) died at scaffold time with a schema error. The scaffold
was not the only derivation either: ``setup`` / ``start`` / ``stop`` / ``status`` and the
secrets env-file each derived the slug from the directory name on their own.

Rulings this contract binds: ``docs/plans/v2/receipts/2026-10-31-165/RULING-568-slug.md``
(F1 python-slugify with ``separator="_"``; F2 the normaliser lives beside ``SLUG_PATTERN``;
F3 an existing lore.yaml's ``project.slug`` wins; F4 a slug owned by another project path is
refused; F5 refusals return ``_EXIT_ERROR`` with a stderr line, never a traceback).

The contract, from the operator's side:

* **Derivation (F1).** A directory name that HAS a valid slug scaffolds a ``lore.yaml``
  whose ``project.slug`` is python-slugify's ``separator="_"`` form of the name: case-folded,
  every run of separators one ``_``, leading/trailing separators stripped, non-ASCII
  transliterated. That file loads under the REAL ``LoreConfig`` (``load_config``). The slug
  keeps every ASCII letter and digit of the name, in order, and adds none: nothing is
  truncated or forged through the YAML template.
* **Refusal (F5).** A name with NO valid slug (nothing but punctuation) is refused LOUDLY:
  ``_EXIT_ERROR``, a stderr line naming the directory, the field and the file, no traceback.
  It leaves no ``lore.yaml`` behind. For EVERY name, a scaffold leaves a loadable lore.yaml or
  none.
* **Agreement (F3).** Every slug a verb uses (secrets env-file, container name, manifest,
  ``.mcp.json`` key, cold-index config) is the ``project.slug`` the lore.yaml declares,
  whether it is the directory-derived slug or an operator's hand edit.
* **Collision (F4 + addendum).** ``setup`` records the project path it provisions as a
  manifest ``meta`` row ``project_path``. A slug held by a DIFFERENT project path (a
  container mounting it, or a manifest recording it) is refused with ``_EXIT_ERROR``, naming
  the slug, this path and the holder's path. A legacy manifest without the row is refused as
  an unknown owner on a FRESH setup (no lore.yaml); a project whose lore.yaml declares the slug
  owns it, so setup BACKFILLS the row and proceeds (directive #18015). One rule for both
  doors: a directory-derived slug and a hand-set lore.yaml slug. A refusal creates,
  rewrites and removes nothing. The same project re-running ``setup`` is not refused.
* **No existing deployment changes.** An already-valid directory name derives itself, and an
  existing lore.yaml is never rewritten.

Run from this directory::

    uv run python -m pytest test_scaffold_slug.py -q
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import string
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import lore_deploy
import pytest
import yaml
from config_reader_fake import realistic_config_document, write_config_document
from loremaster.config import SLUG_PATTERN, load_config

# ---------------------------------------------------------------------------
# Fixture data. Expected slugs are HAND-COMPUTED from the requirement and the F1 ruling
# (python-slugify, ``separator="_"``), never from any implementation's formula.
# ---------------------------------------------------------------------------

#: Directory name → the slug the requirement demands. Real repo names first (measured on
#: this host 2026-10-31: ``~/PycharmProjects/pp-odoo``, and the two names in the #568
#: report), then one row per separator class and per YAML-typing hazard.
VALID_NAME_TO_SLUG: dict[str, str] = {
    "odoo-custom": "odoo_custom",  # the #568 report's own example
    "transcribe-craig": "transcribe_craig",  # the #568 report's own example
    "pp-odoo": "pp_odoo",  # a real repo dir on this host
    "PP-Odoo": "pp_odoo",  # capitals AND a hyphen
    "LoreMaster": "loremaster",  # capitals only: a "replace hyphens" build misses this
    "my.project": "my_project",  # a dot separator
    "My Project": "my_project",  # a space separator
    "2026-forecast": "2026_forecast",  # a leading digit is legal under SLUG_PATTERN
    "2026": "2026",  # all digits: an unquoted YAML scalar would load as an INT
    # Already-valid names derive THEMSELVES: the two live deployments on this host
    # (containers lore-lore / lore-demand_intelligence, measured 2026-10-31).
    "lore": "lore",
    "demand_intelligence": "demand_intelligence",
}

#: Edge names whose slug the F1 ruling (python-slugify, ``separator="_"``) decides: strip
#: leading/trailing separators, collapse separator runs, transliterate. A hand-rolled
#: per-character map (``_private`` refused, ``odoo__custom``, ``caf_``) fails these.
#: The last three are HOSTILE: they try to truncate or forge the YAML the slug is rendered into.
RULED_EDGE_NAME_TO_SLUG: dict[str, str] = {
    "_private": "private",  # leading separator stripped
    ".config": "config",  # leading dot stripped
    "project-": "project",  # trailing separator stripped
    "odoo--custom": "odoo_custom",  # a separator run collapses to one "_"
    "café": "cafe",  # non-ASCII transliterated
    "lore #2": "lore_2",  # `slug: lore #2` in raw YAML is the string "lore": a truncation
    # A newline + a forged YAML key ("/" is impossible in a dir name).
    "demo\n  root: elsewhere": "demo_root_elsewhere",
    "proj: ect": "proj_ect",  # a mapping separator inside the name
}

#: Every name that has a valid slug, with the slug it must scaffold.
ALL_NAME_TO_SLUG: dict[str, str] = {**VALID_NAME_TO_SLUG, **RULED_EDGE_NAME_TO_SLUG}

#: Names with NO valid slug: no letter or digit at all, so the normaliser has nothing to build
#: a slug from. Each MUST be refused.
NO_VALID_SLUG_NAMES: tuple[str, ...] = ("---", "...", "_-_")

#: The #568 headline project: a real hyphenated repo name and its required slug.
HEADLINE_NAME = "odoo-custom"
HEADLINE_SLUG = VALID_NAME_TO_SLUG[HEADLINE_NAME]
#: An operator's hand-edited slug for the same directory (F3: the config wins). Valid, and
#: deliberately NOT the directory-derived slug.
HAND_EDITED_SLUG = "odoo"
#: Both configured-slug cases every agreement pin runs over.
CONFIGURED_SLUGS: tuple[str, ...] = (HEADLINE_SLUG, HAND_EDITED_SLUG)

#: The scaffold always emits ``root: .``; a forged name must not change it.
SCAFFOLD_PROJECT_ROOT = "."

#: Rows in the synthetic manifest ``status`` reads (a state → count rollup).
MANIFEST_INDEXED_ROWS = 3
MANIFEST_STATE = "indexed"

#: The manifest schema the indexer creates (measured 2026-10-31 on
#: ``~/.local/state/lore/{lore,demand_intelligence}.db``): ``meta`` is a key/value table.
MANIFEST_SCHEMA: tuple[str, ...] = (
    """CREATE TABLE IF NOT EXISTS files (
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
)""",
    """CREATE TABLE IF NOT EXISTS meta (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
)""",
)
#: The ``meta`` keys a live manifest already carries (measured, same files).
MANIFEST_LEGACY_META: dict[str, str] = {
    "embedding_schema_fingerprint": "f" * 64,
    "schema_rebuild_status": '{"state": "done"}',
}
#: The ``meta`` key ``setup`` records the owning project path under (ruling addendum F4b).
PROJECT_PATH_META_KEY = "project_path"
#: The refusal text for a slug whose manifest records no owner (ruling addendum: pinned text).
UNKNOWN_OWNER_TEXT = "unknown owner"

#: The container mount the project is served from (``_launch_container``: ``-v <project>:/workspace:ro``).
CONTAINER_WORKSPACE = "/workspace"
#: podman verbs that create, change or remove a container. A refused setup issues none of them.
PODMAN_MUTATING_VERBS = frozenset({"run", "start", "stop", "rm", "kill", "restart", "create"})

_ASCII_ALNUM = frozenset(string.ascii_lowercase + string.digits)


# ---------------------------------------------------------------------------
# Hermetic environment.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _hermetic_deploy_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point every host-global path at ``tmp_path`` and give the template's secrets dummies.

    * ``_loremaster_python`` → the test interpreter (it can import loremaster), so the
      scaffold's checks and every ``_read_config_field`` run for REAL, hermetically.
    * ``MANIFEST_DIR`` / ``LORE_SECRETS_DIR`` → tmp, so no test reads or writes the host's
      real manifests or secrets.
    * ``load_config`` resolves ``anthropic.api_key_env`` eagerly, so it needs a value.
    """
    monkeypatch.setattr(lore_deploy, "_loremaster_python", lambda: sys.executable)
    monkeypatch.setattr(lore_deploy, "MANIFEST_DIR", tmp_path / "state")
    monkeypatch.setattr(lore_deploy, "LORE_SECRETS_DIR", tmp_path / "lore-secrets")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic-key")
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "root")
    monkeypatch.setenv("LORE_TEI_KEY", "dummy-tei-key")


class _GoTemplateSubset:
    """Renders the small subset of podman's Go templates a deploy script plausibly uses.

    Supported: ``{{.A.B}}``, ``{{json .}}`` / ``{{json .A}}``, and ``{{range .Mounts}}…{{end}}``
    whose body uses ``{{.Field}}`` and ``{{if eq .Field "v"}}…{{end}}``. Anything else
    raises, so an unsupported query fails LOUDLY in the test instead of reading as "no
    container".
    """

    _RANGE = re.compile(r"\{\{\s*range\s+\.Mounts\s*\}\}(.*?)\{\{\s*end\s*\}\}(?!.*\{\{\s*end)", re.DOTALL)
    _IF_EQ = re.compile(
        r'\{\{\s*if\s+eq\s+\.(\w+)\s+"([^"]*)"\s*\}\}(.*?)\{\{\s*end\s*\}\}', re.DOTALL
    )
    _JSON = re.compile(r"\{\{\s*json\s+\.([\w.]*)\s*\}\}")
    _FIELD = re.compile(r"\{\{\s*\.([\w.]+)\s*\}\}")

    @classmethod
    def render(cls, template: str, document: dict[str, Any]) -> str:
        """Render ``template`` against one inspect ``document``."""

        def range_body(match: re.Match[str]) -> str:
            return "".join(cls._render_scalar(match.group(1), mount) for mount in document["Mounts"])

        rendered = cls._RANGE.sub(range_body, template)
        rendered = cls._render_scalar(rendered, document)
        if "{{" in rendered:
            raise AssertionError(
                f"PodmanShim cannot render podman format {template!r}; extend _GoTemplateSubset"
            )
        return rendered

    @classmethod
    def _render_scalar(cls, template: str, scope: dict[str, Any]) -> str:
        template = cls._IF_EQ.sub(
            lambda m: m.group(3) if str(scope.get(m.group(1))) == m.group(2) else "", template
        )
        template = cls._JSON.sub(lambda m: json.dumps(cls._lookup(scope, m.group(1))), template)
        return cls._FIELD.sub(lambda m: str(cls._lookup(scope, m.group(1))), template)

    @staticmethod
    def _lookup(scope: dict[str, Any], dotted: str) -> Any:
        value: Any = scope
        for part in filter(None, dotted.split(".")):
            value = value[part]
        return value


@dataclass
class PodmanShim:
    """Stands in for podman (and the cold index) at the ``_run`` seam; runs everything else.

    ``podman container inspect`` answers from ONE optional container (its state and the host
    path mounted at ``/workspace``), in the JSON shape podman prints (keys measured on
    ``lore-demand_intelligence`` 2026-10-31), with or without ``--format``. ``image exists`` and
    the mutating verbs succeed and are recorded. Any OTHER podman command raises, so a query
    the shim does not model fails loudly instead of reading as "absent". The cold index
    (``-m loremaster.index``) is recorded and answered as success. EVERY OTHER command
    delegates to the real ``_run``, so config reads, the normaliser and ``merge_mcp_json.py`` run
    for real and the ``.mcp.json`` on disk is the observable outcome.
    """

    real_run: Callable[..., subprocess.CompletedProcess[str]]
    container_state: str | None = None
    workspace_source: str | None = None
    podman_calls: list[list[str]] = field(default_factory=list)
    index_calls: list[list[str]] = field(default_factory=list)

    def __call__(
        self, cmd: list[str], *, check: bool = True, capture: bool = False
    ) -> subprocess.CompletedProcess[str]:
        """Record-and-answer podman / the cold index; delegate everything else."""
        if cmd and cmd[0] == "podman":
            self.podman_calls.append(list(cmd))
            return self._answer_podman(cmd)
        if "loremaster.index" in cmd:
            self.index_calls.append(list(cmd))
            self._index_like_the_real_indexer(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return self.real_run(cmd, check=check, capture=capture)

    @staticmethod
    def _index_like_the_real_indexer(cmd: list[str]) -> None:
        """Create the manifest the real cold index creates: ``<slug>.db`` with its schema.

        ``CREATE TABLE IF NOT EXISTS`` and no ``project_path`` row: the indexer never writes
        the owner (``setup`` does), and a row ``setup`` wrote before indexing survives.
        """
        config_path = Path(cmd[cmd.index("--config") + 1])
        slug = yaml.safe_load(config_path.read_text(encoding="utf-8"))["project"]["slug"]
        _create_manifest(slug, owner=None, indexed_rows=MANIFEST_INDEXED_ROWS)

    def _inspect_document(self, name: str) -> dict[str, Any]:
        mounts: list[dict[str, Any]] = []
        if self.workspace_source is not None:
            mounts.append(
                {
                    "Type": "bind",
                    "Source": self.workspace_source,
                    "Destination": CONTAINER_WORKSPACE,
                    "Mode": "",
                    "RW": False,
                    "Propagation": "rprivate",
                }
            )
        mounts.append(
            {
                "Type": "bind",
                "Source": str(lore_deploy.MANIFEST_DIR),
                "Destination": lore_deploy.CONTAINER_STATE_DIR,
                "Mode": "",
                "RW": True,
                "Propagation": "rprivate",
            }
        )
        return {
            "Name": name,
            "State": {"Status": self.container_state},
            "Image": "0" * 64,
            "ImageName": lore_deploy.IMAGE,
            "Mounts": mounts,
        }

    def _answer_podman(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        verb = cmd[1]
        if verb in PODMAN_MUTATING_VERBS or cmd[1:3] == ["image", "exists"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[1:3] == ["container", "inspect"] or verb == "inspect":
            if self.container_state is None:
                return subprocess.CompletedProcess(cmd, 125, stdout="", stderr="no such container")
            document = self._inspect_document(cmd[-1])
            if "--format" in cmd:
                template = cmd[cmd.index("--format") + 1]
                stdout = _GoTemplateSubset.render(template, document) + "\n"
            else:
                stdout = json.dumps([document])
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        raise AssertionError(f"PodmanShim does not model {cmd!r}; extend it")

    def container_names(self) -> list[str]:
        """Every container name any podman call addressed (image calls excluded)."""
        names: list[str] = []
        for cmd in self.podman_calls:
            if cmd[1] == "image":
                continue
            if cmd[1] == "run":
                names.append(cmd[cmd.index("--name") + 1])
            else:
                names.append(cmd[-1])
        return names

    def mutating_calls(self) -> list[list[str]]:
        """Every podman call that would create, change or remove a container."""
        return [cmd for cmd in self.podman_calls if cmd[1] in PODMAN_MUTATING_VERBS]

    @classmethod
    def install(
        cls,
        monkeypatch: pytest.MonkeyPatch,
        *,
        container_state: str | None,
        workspace_source: Path | None = None,
    ) -> PodmanShim:
        """Install the shim over ``lore_deploy._run``."""
        shim = cls(
            real_run=lore_deploy._run,
            container_state=container_state,
            workspace_source=None if workspace_source is None else str(workspace_source),
        )
        monkeypatch.setattr(lore_deploy, "_run", shim)
        return shim


def _stub_network_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arrange the embed / store / bind / artifact probes as passing; none touches a network.

    The scaffold writes the PRODUCTION store URL (``:18500``); the root conftest guard fails
    any test that dials it, and these stubs are what keep every verb here off it.
    """
    ok = lambda *args, **kwargs: lore_deploy._EXIT_OK  # noqa: E731 - a one-line stub
    monkeypatch.setattr(lore_deploy, "_probe_embed", ok)
    monkeypatch.setattr(lore_deploy, "_probe_surreal", ok)
    monkeypatch.setattr(lore_deploy, "_await_bind", ok)
    monkeypatch.setattr(lore_deploy, "_probe_container_binaries", ok)
    monkeypatch.setattr(lore_deploy, "_probe_workspace_honesty", ok)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------
def _project_dir(tmp_path: Path, name: str, parent: str = "projects") -> Path:
    """Create ``<tmp>/<parent>/<name>`` (the name is the slug source)."""
    project = tmp_path / parent / name
    project.mkdir(parents=True)
    return project


def _scaffold_or_fail(project: Path) -> Path:
    """Scaffold ``project``'s lore.yaml; a raise is a contract FAILURE naming the name."""
    config_path = project / "lore.yaml"
    try:
        lore_deploy._scaffold_lore_yaml(project, config_path)
    except Exception as error:  # noqa: BLE001 - any raise is the defect under test
        pytest.fail(
            f"scaffolding a project named {project.name!r} raised {error!r}; a directory "
            f"name with a valid slug must scaffold a loadable lore.yaml (#568)"
        )
    return config_path


def _write_operator_config(project: Path, slug: str) -> Path:
    """Write a production-shaped lore.yaml declaring ``slug`` (the shared config builder)."""
    return write_config_document(realistic_config_document(slug=slug), project / "lore.yaml")


def _write_env_file(tmp_path: Path) -> Path:
    env_file = tmp_path / "secrets.env"
    env_file.write_text("LORE_TEI_KEY=dummy-tei-key\n", encoding="utf-8")
    return env_file


def _create_manifest(slug: str, *, owner: Path | None, indexed_rows: int) -> Path:
    """Create (or extend) ``<slug>.db`` in the production schema.

    ``owner`` is the ``project_path`` row; ``None`` writes no row (a legacy manifest, as every
    live manifest was on 2026-10-31). Existing rows are kept, never overwritten.
    """
    lore_deploy.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest = lore_deploy.MANIFEST_DIR / f"{slug}.db"
    with sqlite3.connect(manifest) as connection:
        for statement in MANIFEST_SCHEMA:
            connection.execute(statement)
        meta = dict(MANIFEST_LEGACY_META)
        if owner is not None:
            meta[PROJECT_PATH_META_KEY] = str(owner)
        connection.executemany("INSERT OR IGNORE INTO meta VALUES (?, ?)", meta.items())
        connection.executemany(
            "INSERT OR IGNORE INTO files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (slug, f"module_{index}.py", "0" * 128, 0, 1, 1, "[]", MANIFEST_STATE,
                 "2026-10-31T00:00:00Z")
                for index in range(indexed_rows)
            ],
        )
    return manifest


def _write_manifest(slug: str, *, owner: Path | None) -> Path:
    """A provisioned project's manifest for ``slug``; ``owner=None`` is a legacy manifest."""
    return _create_manifest(slug, owner=owner, indexed_rows=MANIFEST_INDEXED_ROWS)


def _manifest_owner(slug: str) -> str | None:
    """The ``project_path`` row of ``<slug>.db`` (None: no manifest, or no row)."""
    manifest = lore_deploy.MANIFEST_DIR / f"{slug}.db"
    if not manifest.exists():
        return None
    with sqlite3.connect(f"file:{manifest}?mode=ro", uri=True) as connection:
        row = connection.execute(
            "SELECT v FROM meta WHERE k = ?", (PROJECT_PATH_META_KEY,)
        ).fetchone()
    return None if row is None else str(row[0])


def _mcp_server_keys(project: Path) -> list[str]:
    """The ``lore_*`` server keys in ``project/.mcp.json`` (empty when absent)."""
    mcp_json = project / ".mcp.json"
    if not mcp_json.exists():
        return []
    servers = json.loads(mcp_json.read_text(encoding="utf-8")).get("mcpServers", {})
    return sorted(key for key in servers if key.startswith("lore_"))


def _ascii_alnum_sequence(text: str) -> list[str]:
    """The ASCII letters and digits of ``text``, case-folded, in order."""
    return [char for char in text.lower() if char in _ASCII_ALNUM]


def _names_path(message: str, path: Path) -> bool:
    """Whether ``message`` names ``path`` (as given, or resolved)."""
    return str(path) in message or str(path.resolve()) in message


@dataclass
class VerbOutcome:
    """What one verb call did: its exit code or raise, and its streams."""

    return_code: int | None
    raised: BaseException | None
    stdout: str
    stderr: str


def _drive(call: Callable[[], int], capsys: pytest.CaptureFixture[str]) -> VerbOutcome:
    """Run a verb and capture its exit OR its raise (both are operator-visible)."""
    return_code: int | None = None
    raised: BaseException | None = None
    try:
        return_code = call()
    except Exception as error:  # noqa: BLE001 - a raise is an outcome to classify
        raised = error
    captured = capsys.readouterr()
    return VerbOutcome(return_code, raised, captured.out, captured.err)


def _drive_setup(project: Path, env_file: Path, capsys: pytest.CaptureFixture[str]) -> VerbOutcome:
    """Run ``verb_setup`` and capture its exit or its raise."""
    return _drive(lambda: lore_deploy.verb_setup(project, env_file), capsys)


def _assert_refused_with_exit_error(outcome: VerbOutcome, what: str) -> None:
    """F5: a refusal is ``_EXIT_ERROR`` plus a stderr line, never a raise."""
    assert outcome.raised is None, (
        f"{what} must be refused with _EXIT_ERROR and a stderr line, not a raise; "
        f"raised {outcome.raised!r}"
    )
    assert outcome.return_code == lore_deploy._EXIT_ERROR, (
        f"{what} must return _EXIT_ERROR ({lore_deploy._EXIT_ERROR}); got "
        f"{outcome.return_code}, stdout: {outcome.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Derivation.
# ---------------------------------------------------------------------------
class TestScaffoldDerivesTheSlugFromTheDirectoryName:
    """A directory name with a valid slug scaffolds a lore.yaml the real config loads."""

    @pytest.mark.parametrize(("name", "expected_slug"), sorted(ALL_NAME_TO_SLUG.items()))
    def test_scaffolded_slug_is_the_slugified_directory_name(
        self, tmp_path: Path, name: str, expected_slug: str
    ) -> None:
        """``odoo-custom`` → ``odoo_custom``; ``_private`` → ``private``; ``lore`` → ``lore``."""
        config_path = _scaffold_or_fail(_project_dir(tmp_path, name))

        config = load_config(config_path)

        assert config.project.slug == expected_slug, (
            f"directory {name!r} must scaffold project.slug {expected_slug!r} "
            f"(python-slugify, separator '_'); got {config.project.slug!r}"
        )
        # The store database is the slug's main consumer: it must follow the same slug.
        assert config.effective_surreal_database == expected_slug, (
            f"the store database for {name!r} must be the slug {expected_slug!r}; "
            f"got {config.effective_surreal_database!r}"
        )


class TestEveryNameScaffoldsAValidLoreYamlOrNone:
    """∀ names: the scaffold leaves a loadable lore.yaml, or raises loudly and leaves none.

    A half-written lore.yaml is the worst outcome: the next ``setup`` sees the file, skips the
    scaffold, and fails later on a config nobody wrote on purpose.
    """

    @pytest.mark.parametrize("name", sorted({*ALL_NAME_TO_SLUG, *NO_VALID_SLUG_NAMES}))
    def test_scaffold_outcome_is_valid_or_nothing(self, tmp_path: Path, name: str) -> None:
        """A raise leaves no lore.yaml; a write is loadable, on-pattern and unforged."""
        project = _project_dir(tmp_path, name)
        config_path = project / "lore.yaml"

        try:
            lore_deploy._scaffold_lore_yaml(project, config_path)
        except Exception as error:  # noqa: BLE001 - a raise is an allowed outcome here
            assert not config_path.exists(), (
                f"scaffolding {name!r} raised ({error}) but LEFT a lore.yaml behind; the "
                f"next setup would skip the scaffold and run on a config that never validated"
            )
            # Verbatim or repr'd (a repr escapes a newline in the name; both identify it).
            assert name in str(error) or repr(name) in str(error), (
                f"the refusal for {name!r} must name the directory; got: {error}"
            )
            return

        config = load_config(config_path)
        slug = config.project.slug
        assert re.fullmatch(SLUG_PATTERN, slug), f"slug {slug!r} for {name!r} violates SLUG_PATTERN"
        assert config.project.root == SCAFFOLD_PROJECT_ROOT, (
            f"directory {name!r} changed project.root to {config.project.root!r}: the name "
            f"was rendered into the YAML unescaped and forged another key"
        )

    @pytest.mark.parametrize("name", sorted(name for name in ALL_NAME_TO_SLUG if name.isascii()))
    def test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order(
        self, tmp_path: Path, name: str
    ) -> None:
        """No letter or digit of an ASCII name is dropped or invented (e.g. ``lore #2``)."""
        config_path = _scaffold_or_fail(_project_dir(tmp_path, name))

        slug = load_config(config_path).project.slug

        assert _ascii_alnum_sequence(slug) == _ascii_alnum_sequence(name), (
            f"directory {name!r} scaffolded slug {slug!r}: its letters/digits "
            f"{''.join(_ascii_alnum_sequence(slug))!r} differ from the name's "
            f"{''.join(_ascii_alnum_sequence(name))!r} (truncated, forged or invented)"
        )


# ---------------------------------------------------------------------------
# Refusal (F5).
# ---------------------------------------------------------------------------
class TestANameWithNoValidSlugIsRefusedLoudly:
    """``setup`` on a name with nothing to build a slug from refuses and changes nothing."""

    @pytest.mark.parametrize("name", NO_VALID_SLUG_NAMES)
    def test_setup_refuses_naming_the_directory_and_writes_nothing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        name: str,
    ) -> None:
        """``_EXIT_ERROR``, a stderr line naming dir + field + file, no lore.yaml, no index."""
        project = _project_dir(tmp_path, name)
        env_file = _write_env_file(tmp_path)
        # Probes pass, so a build that MANGLES the name into some slug and carries on
        # would reach the cold index; only a refusal stops before it.
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(project, env_file, capsys)

        _assert_refused_with_exit_error(outcome, f"setup on {name!r} (no valid slug)")
        assert name in outcome.stderr, (
            f"the refusal must name the directory {name!r} on stderr; got: {outcome.stderr!r}"
        )
        # The remedy (ruling F1): set project.slug by hand in lore.yaml (or rename the dir).
        assert "slug" in outcome.stderr and "lore.yaml" in outcome.stderr, (
            f"the refusal must name the field (slug) and the file (lore.yaml) the operator "
            f"can write by hand; got: {outcome.stderr!r}"
        )
        assert not (project / "lore.yaml").exists(), (
            f"a refused setup on {name!r} must leave NO lore.yaml, or the next setup skips "
            f"the scaffold and runs on a config that never validated"
        )
        assert shim.index_calls == [], f"a refused setup must not cold-index; ran {shim.index_calls}"
        assert _mcp_server_keys(project) == [], "a refused setup must not wire .mcp.json"

    def test_main_returns_exit_error_for_an_unslugifiable_dir_not_a_traceback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The CLI door: ``lore_deploy setup --project …/---`` exits ``_EXIT_ERROR``, no raise.

        ``main`` resolves slug consumers (the env-file path) before dispatching; a resolver
        that raises there would crash the CLI with a traceback ahead of every friendly check.
        """
        project = _project_dir(tmp_path, NO_VALID_SLUG_NAMES[0])
        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        _stub_network_probes(monkeypatch)
        PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive(lambda: lore_deploy.main(["setup", "--project", str(project)]), capsys)

        _assert_refused_with_exit_error(outcome, f"`setup --project {project}`")
        assert not (project / "lore.yaml").exists()

    def test_main_reports_a_missing_project_dir_before_resolving_its_slug(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A missing ``--project`` whose name has no slug gets the not-a-directory refusal."""
        missing = tmp_path / "absent" / NO_VALID_SLUG_NAMES[0]
        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive(lambda: lore_deploy.main(["status", "--project", str(missing)]), capsys)

        _assert_refused_with_exit_error(outcome, f"`status --project {missing}` (missing dir)")
        assert _names_path(outcome.stderr, missing), (
            f"the refusal must name the missing directory {missing}; got: {outcome.stderr!r}"
        )


# ---------------------------------------------------------------------------
# Agreement (F3): every verb uses the slug the lore.yaml declares.
# ---------------------------------------------------------------------------
class TestSetupProvisionsAHyphenatedProjectEndToEnd:
    """The #568 path: ``setup`` on ``odoo-custom`` with no lore.yaml provisions it."""

    def test_setup_scaffolds_indexes_and_wires_under_the_derived_slug(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit OK; lore.yaml loads with ``odoo_custom``; index + .mcp.json use it."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        env_file = _write_env_file(tmp_path)
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(project, env_file, capsys)

        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
            f"setup on {HEADLINE_NAME!r} must provision; got rc={outcome.return_code} "
            f"raised={outcome.raised!r} stderr={outcome.stderr!r}"
        )
        config_path = project / "lore.yaml"
        assert load_config(config_path).project.slug == HEADLINE_SLUG
        assert len(shim.index_calls) == 1 and str(config_path) in shim.index_calls[0], (
            f"setup must cold-index once against the scaffolded config; ran {shim.index_calls}"
        )
        assert _mcp_server_keys(project) == [f"lore_{HEADLINE_SLUG}"], (
            f".mcp.json must carry exactly the lore_{HEADLINE_SLUG} server; "
            f"got {_mcp_server_keys(project)}"
        )


@pytest.mark.parametrize("configured_slug", CONFIGURED_SLUGS)
class TestEveryVerbUsesTheConfiguredSlug:
    """For ``odoo-custom``, every verb uses the lore.yaml's ``project.slug``, never the dir name.

    Two configs: the directory-derived ``odoo_custom`` (what the scaffold writes) and an
    operator's hand edit ``odoo`` (ruling F3: the config wins). Both go RED on any verb that
    still uses the raw name; the hand edit also goes RED on a verb that re-derives the slug
    from the directory instead of reading the config.
    """

    def test_env_file_resolves_under_the_configured_slug(
        self, tmp_path: Path, configured_slug: str
    ) -> None:
        """The per-slug secrets file is ``<slug>.env``, not ``<dir name>.env``."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, configured_slug)

        resolved = lore_deploy._resolve_env_file(project, None)

        expected = lore_deploy.LORE_SECRETS_DIR / f"{configured_slug}.env"
        assert Path(resolved) == expected, f"env-file must be {expected}; got {resolved}"

    def test_start_names_its_container_and_mcp_key_after_the_slug(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, configured_slug: str
    ) -> None:
        """Fresh launch: every podman call addresses ``lore-<slug>``; .mcp.json ``lore_<slug>``."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, configured_slug)
        env_file = _write_env_file(tmp_path)
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        return_code = lore_deploy.verb_start(project, env_file)

        assert return_code == lore_deploy._EXIT_OK
        names = shim.container_names()
        assert names and set(names) == {f"lore-{configured_slug}"}, (
            f"start must address only container lore-{configured_slug}; addressed {names}"
        )
        assert _mcp_server_keys(project) == [f"lore_{configured_slug}"], (
            f"start must wire exactly lore_{configured_slug}; got {_mcp_server_keys(project)}"
        )

    def test_stop_stops_the_container_start_names(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, configured_slug: str
    ) -> None:
        """``stop`` inspects, stops and removes ``lore-<slug>``: the one ``start`` made."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, configured_slug)
        shim = PodmanShim.install(monkeypatch, container_state="running", workspace_source=project)

        return_code = lore_deploy.verb_stop(project)

        assert return_code == lore_deploy._EXIT_OK
        names = shim.container_names()
        assert set(names) == {f"lore-{configured_slug}"}, (
            f"stop must address only container lore-{configured_slug}; addressed {names}"
        )
        assert any(cmd[1] == "stop" for cmd in shim.podman_calls), (
            f"a running container must be stopped; podman calls: {shim.podman_calls}"
        )

    def test_status_reads_the_manifest_the_slug_names(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        configured_slug: str,
    ) -> None:
        """A provisioned project's manifest (``<slug>.db``) is found and summarised."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, configured_slug)
        manifest = _write_manifest(configured_slug, owner=project)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        lore_deploy.verb_status(project)

        out = capsys.readouterr().out
        assert f"{MANIFEST_STATE}={MANIFEST_INDEXED_ROWS}" in out, (
            f"status must summarise the manifest at {manifest} "
            f"({MANIFEST_STATE}={MANIFEST_INDEXED_ROWS}); stdout: {out!r}"
        )
        assert set(shim.container_names()) == {f"lore-{configured_slug}"}, (
            f"status must inspect lore-{configured_slug}; addressed {shim.container_names()}"
        )

    def test_setup_recognises_a_provisioned_project_and_rewires_its_slug(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        configured_slug: str,
    ) -> None:
        """Config + ``<slug>.db`` present → no-op success, no re-index, .mcp.json ``lore_<slug>``.

        The env-file is deliberately ABSENT: a setup that looks for the manifest under any
        other slug misses the provisioned project, falls through to the env-file check and
        fails, instead of re-running the expensive cold index.
        """
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, configured_slug)
        _write_manifest(configured_slug, owner=project)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(project, tmp_path / "absent.env", capsys)

        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
            f"setup must recognise the provisioned {configured_slug} project; got "
            f"rc={outcome.return_code} raised={outcome.raised!r} stderr={outcome.stderr!r}"
        )
        assert shim.index_calls == [], "a provisioned project must not be re-indexed"
        assert _mcp_server_keys(project) == [f"lore_{configured_slug}"]


# ---------------------------------------------------------------------------
# Collision (F4 + addendum): a slug held by another project path is refused.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SlugDoor:
    """How a project arrives at its slug: derived from its directory, or hand-set in lore.yaml."""

    label: str
    hand_set_slug: str | None

    @property
    def slug(self) -> str:
        """The slug ``setup`` resolves through this door for ``HEADLINE_NAME``."""
        return self.hand_set_slug if self.hand_set_slug is not None else HEADLINE_SLUG


#: Ruling addendum (class lift): ONE collision rule for both doors.
SLUG_DOORS: tuple[SlugDoor, ...] = (
    SlugDoor("derived", None),  # no lore.yaml: odoo-custom → odoo_custom
    SlugDoor("hand_set", HAND_EDITED_SLUG),  # lore.yaml declares odoo
)


@dataclass
class CollisionScene:
    """One project at ``HEADLINE_NAME`` arriving through ``door``, plus a holder elsewhere."""

    door: SlugDoor
    project: Path
    other_project: Path
    env_file: Path
    config_before: bytes | None

    @classmethod
    def build(cls, tmp_path: Path, door: SlugDoor) -> CollisionScene:
        """Create both project dirs; write the hand-set lore.yaml when the door is hand_set."""
        other_project = _project_dir(tmp_path, door.slug, parent="elsewhere")
        project = _project_dir(tmp_path, HEADLINE_NAME)
        config_before = None
        if door.hand_set_slug is not None:
            config_before = _write_operator_config(project, door.hand_set_slug).read_bytes()
        return cls(door, project, other_project, _write_env_file(tmp_path), config_before)

    def assert_nothing_created(self, shim: PodmanShim) -> None:
        """A refused setup writes no lore.yaml (or leaves the existing one byte-identical),
        no index, no .mcp.json, and touches no container."""
        config_path = self.project / "lore.yaml"
        if self.config_before is None:
            assert not config_path.exists(), "a refused setup must not scaffold lore.yaml"
        else:
            assert config_path.read_bytes() == self.config_before, (
                "a refused setup must not rewrite the existing lore.yaml"
            )
        assert shim.index_calls == [], f"a refused setup must not cold-index; ran {shim.index_calls}"
        assert _mcp_server_keys(self.project) == [], "a refused setup must not wire .mcp.json"
        assert shim.mutating_calls() == [], (
            f"a refused setup must not create/stop/remove any container; ran {shim.mutating_calls()}"
        )

    def assert_refusal_names(self, outcome: VerbOutcome, *, holder: Path | None) -> None:
        """``_EXIT_ERROR``; stderr names the slug, THIS path, and the holder (or 'unknown owner')."""
        _assert_refused_with_exit_error(
            outcome, f"setup on {self.project} ({self.door.label} slug {self.door.slug!r} is held)"
        )
        assert self.door.slug in outcome.stderr, (
            f"must name the slug {self.door.slug!r}; got {outcome.stderr!r}"
        )
        assert _names_path(outcome.stderr, self.project), (
            f"must name this project {self.project}; got {outcome.stderr!r}"
        )
        if holder is None:
            assert UNKNOWN_OWNER_TEXT in outcome.stderr, (
                f"a manifest with no {PROJECT_PATH_META_KEY} row must be refused as "
                f"{UNKNOWN_OWNER_TEXT!r}; got {outcome.stderr!r}"
            )
        else:
            assert _names_path(outcome.stderr, holder), (
                f"must name the holding project {holder}; got {outcome.stderr!r}"
            )


@pytest.mark.parametrize("door", SLUG_DOORS, ids=lambda door: door.label)
class TestSetupRefusesASlugHeldByAnotherProject:
    """A slug another project path holds is refused, whichever door the slug came through.

    ``odoo-custom`` and ``odoo_custom`` (or ``Lore`` and ``lore``) derive the SAME slug, and
    an operator can hand-set a slug another project already uses. A shared slug means a shared
    store database, manifest, container and secrets file.
    """

    def test_refuses_when_the_slugs_container_serves_another_project(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        door: SlugDoor,
    ) -> None:
        """Container ``lore-<slug>`` mounts ``…/elsewhere/<slug>`` → refuse, naming both paths."""
        scene = CollisionScene.build(tmp_path, door)
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(
            monkeypatch, container_state="running", workspace_source=scene.other_project
        )

        outcome = _drive_setup(scene.project, scene.env_file, capsys)

        scene.assert_refusal_names(outcome, holder=scene.other_project)
        scene.assert_nothing_created(shim)

    def test_refuses_when_the_slugs_manifest_records_another_project(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        door: SlugDoor,
    ) -> None:
        """A STOPPED holder (no container): its manifest's ``project_path`` names it → refuse."""
        scene = CollisionScene.build(tmp_path, door)
        manifest = _write_manifest(door.slug, owner=scene.other_project)
        manifest_bytes = manifest.read_bytes()
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(scene.project, scene.env_file, capsys)

        scene.assert_refusal_names(outcome, holder=scene.other_project)
        scene.assert_nothing_created(shim)
        assert manifest.read_bytes() == manifest_bytes, "a refused setup must not touch the manifest"


class TestSetupRecordsAndHonoursItsOwnProjectPath:
    """``setup`` writes ``project_path``; the same project re-running setup is not refused."""

    def test_fresh_setup_records_this_project_path_in_the_manifest(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """After provisioning ``odoo-custom``, ``odoo_custom.db`` meta ``project_path`` is its path."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        env_file = _write_env_file(tmp_path)
        _stub_network_probes(monkeypatch)
        PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(project, env_file, capsys)

        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
            f"setup must provision; got rc={outcome.return_code} raised={outcome.raised!r} "
            f"stderr={outcome.stderr!r}"
        )
        owner = _manifest_owner(HEADLINE_SLUG)
        assert owner is not None, (
            f"setup must record a {PROJECT_PATH_META_KEY!r} meta row in {HEADLINE_SLUG}.db"
        )
        assert Path(owner).resolve() == project.resolve(), (
            f"{PROJECT_PATH_META_KEY} must be this project {project}; got {owner!r}"
        )

    def test_fresh_setup_refuses_a_legacy_manifest_as_an_unknown_owner(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No lore.yaml here, ``odoo_custom.db`` has no ``project_path`` row, no container → refuse.

        A fresh setup cannot be the legacy manifest's owner re-running: the owner would have a
        lore.yaml. With no container to show a mount, the owner is unknown, and an unknown
        owner is never accepted (ruling addendum F4b).
        """
        scene = CollisionScene.build(tmp_path, SLUG_DOORS[0])
        manifest = _write_manifest(HEADLINE_SLUG, owner=None)
        manifest_bytes = manifest.read_bytes()
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(scene.project, scene.env_file, capsys)

        scene.assert_refusal_names(outcome, holder=None)
        scene.assert_nothing_created(shim)
        assert manifest.read_bytes() == manifest_bytes, "a refused setup must not touch the manifest"

    @pytest.mark.parametrize("configured_slug", CONFIGURED_SLUGS)
    def test_existing_deployment_backfills_its_legacy_manifest_and_proceeds(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        configured_slug: str,
    ) -> None:
        """lore.yaml declares the slug + a legacy ``<slug>.db`` (no row) → backfill, no-op success.

        Every live manifest predated the row (both on this host, measured 2026-10-31), so
        re-running setup on an existing deployment must never be refused (directive #18015).
        No container (a stopped deployment) and an ABSENT env-file: a build that refuses, or that
        falls through past the provisioned check, fails here.
        """
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, configured_slug)
        _write_manifest(configured_slug, owner=None)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(project, tmp_path / "absent.env", capsys)

        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
            f"re-running setup on an existing {configured_slug} deployment must not be refused; "
            f"got rc={outcome.return_code} raised={outcome.raised!r} stderr={outcome.stderr!r}"
        )
        owner = _manifest_owner(configured_slug)
        assert owner is not None and Path(owner).resolve() == project.resolve(), (
            f"setup must backfill {PROJECT_PATH_META_KEY} = {project} into the legacy "
            f"{configured_slug}.db; got {owner!r}"
        )
        assert shim.index_calls == [], "a provisioned project must not be re-indexed"
        assert shim.mutating_calls() == [], f"setup must touch no container; ran {shim.mutating_calls()}"
        assert _mcp_server_keys(project) == [f"lore_{configured_slug}"]

    def test_same_project_rerun_with_its_running_container_is_not_refused(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Its own lore.yaml, manifest (owner = THIS path) and container → provisioned no-op."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, HEADLINE_SLUG)
        _write_manifest(HEADLINE_SLUG, owner=project)
        env_file = _write_env_file(tmp_path)
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(monkeypatch, container_state="running", workspace_source=project)

        outcome = _drive_setup(project, env_file, capsys)

        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
            f"the same project re-running setup must not be refused; got rc={outcome.return_code} "
            f"raised={outcome.raised!r} stderr={outcome.stderr!r}"
        )
        assert shim.index_calls == [], "a provisioned project must not be re-indexed"
        assert shim.mutating_calls() == [], (
            f"setup must not touch its own running container; ran {shim.mutating_calls()}"
        )
        assert _mcp_server_keys(project) == [f"lore_{HEADLINE_SLUG}"]

    def test_same_project_resuming_after_its_scaffold_is_not_refused(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Its lore.yaml exists (an earlier setup stopped after scaffolding) → setup completes."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        _write_operator_config(project, HEADLINE_SLUG)
        env_file = _write_env_file(tmp_path)
        _stub_network_probes(monkeypatch)
        shim = PodmanShim.install(monkeypatch, container_state=None)

        outcome = _drive_setup(project, env_file, capsys)

        assert outcome.raised is None and outcome.return_code == lore_deploy._EXIT_OK, (
            f"a project resuming its own setup must not be refused; got rc={outcome.return_code} "
            f"raised={outcome.raised!r} stderr={outcome.stderr!r}"
        )
        assert len(shim.index_calls) == 1, f"setup must cold-index once; ran {shim.index_calls}"
        assert _mcp_server_keys(project) == [f"lore_{HEADLINE_SLUG}"]
        owner = _manifest_owner(HEADLINE_SLUG)
        assert owner is not None and Path(owner).resolve() == project.resolve(), (
            f"setup must record {PROJECT_PATH_META_KEY} = {project}; got {owner!r}"
        )


# ---------------------------------------------------------------------------
# No existing deployment changes.
# ---------------------------------------------------------------------------
class TestAnExistingLoreYamlIsNeverRewritten:
    """The scaffold runs only when lore.yaml is absent; an operator's slug survives setup."""

    def test_setup_leaves_an_operator_chosen_slug_byte_identical(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``odoo-custom`` whose lore.yaml says ``odoo``: setup must not "correct" it."""
        project = _project_dir(tmp_path, HEADLINE_NAME)
        config_path = _write_operator_config(project, HAND_EDITED_SLUG)
        before = config_path.read_bytes()
        PodmanShim.install(monkeypatch, container_state=None)

        _drive_setup(project, tmp_path / "absent.env", capsys)

        assert config_path.read_bytes() == before, (
            "setup rewrote an existing lore.yaml; the scaffold (and any slug normaliser) "
            "must run only when lore.yaml is absent"
        )
