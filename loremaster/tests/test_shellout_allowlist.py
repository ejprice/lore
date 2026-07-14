"""Contract — finding #125 / #131, LAYER 1: derive the binaries the IMAGE must carry.

The defect this closes is the one the contract-adversary found sitting UNDER the honesty
line: the deployed image has no ``git`` binary, so the CORRECT implementation of #125
serves ``git_branch: null`` in the only environment the feature exists for (and #131 —
every production snapshot's ``git_ref`` has been silently ``None`` for the same reason).
Every test in ``test_workspace_status.py`` runs on a host that HAS git, so no test there
can see it. That is the #107 shape exactly: the fixture guarantees the one condition
under which the bug is invisible.

The instrument is three layers; this file is layer 1, and the other two are deploy probes
(``skills/lore-deploy/tests/test_workspace_probe.py``):

1. **DERIVE the safe set (here).** Not "enumerate what the image must not lose" — that
   set is unbounded, and this repo's most expensive lesson is that a list of forbidden
   names always loses. Instead: walk every process-spawning call site in the SHIPPED
   packages and collect ``argv[0]``. Today that set is exactly ``{"git"}``. Add a
   shell-out tomorrow and the required set GROWS BY ITSELF — nobody has to remember.
2. Deploy probe: every binary in that derived set must exist in the running container.
3. Deploy probe: if a watched root carries a ``.git``, the SERVED branch must be non-null
   (the only layer that can see a git that is present but REFUSING — e.g. git's
   dubious-ownership exit 128, finding #132).

**Coverage is a CHECKED variable, not a hope** (the repo's instrument law: "a runtime gate
is an invariant only over code it RUNS"). Two ways to escape a derivation like this, and
both must FAIL LOUD rather than silently shrink the required set:

* an exec site whose ``argv[0]`` is not a literal (``subprocess.run(cmd)``) — the scan
  cannot know what it launches, so a human must rule;
* a shipped module that CAN spawn a process but yields no resolved site — i.e. the scan
  does not understand the form it used. A silent empty answer there is how a name-list
  loses; the raise is what turns it into a verdict.

The contract this file pins (the shape a builder must land):

* ``loremaster.shellout.required_binaries(repo_root) -> frozenset[str]`` — the derived
  safe set over the uv-workspace members the image installs.
* ``loremaster.shellout.UnresolvedExecSiteError`` — raised, naming the file (and line,
  where there is one), for either escape above. Never a silent skip.

Fixture-value discipline: every synthetic fixture below uses member names and binaries
UNLIKE this repo's own (``alpha``/``beta``/``gamma``, ``rg``/``fd``/``hg`` — never
``loremaster``, never ``git``), so a build that hardcodes either the member list or the
answer ``{"git"}`` fails.

How to run:
    uv run pytest loremaster/tests/test_shellout_allowlist.py -n auto -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from loremaster.shellout import (
    ShelloutScanError,
    UnresolvedExecSiteError,
    required_binaries,
)

# The REAL repo root, resolved from THIS FILE (never from the package's ``__file__``):
# the test tree always lives in the real checkout, even when the package under test is
# PYTHONPATH-shadowed by a scratch build.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# The one external binary lore's shipped code actually execs today
# (``loremaster/loremaster/index/snapshots.py`` — the shared ``capture_git_identity``
# seam). If this file's first test goes RED, the shipped code grew a NEW shell-out: put
# that binary in the image (Containerfile) and update the constant. That RED is the
# instrument working — it is the moment a human must rule on a new dependency.
_TODAYS_DERIVED_SET = frozenset({"git"})

# Deliberately foreign names — a hardcoded ``["lorescribe", "loresigil", "loremaster"]``
# member list or a hardcoded ``{"git"}`` answer must fail every synthetic fixture below.
_ALPHA_BINARY = "rg"
_BETA_BINARY = "fd"
_GAMMA_BINARY = "hg"
_UNSHIPPED_BINARY = "never-in-the-image"


def _write_workspace(root: Path, members: list[str]) -> None:
    """A uv-workspace root pyproject declaring ``members`` — what the image installs."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "synthetic"\nversion = "0.0.0"\n\n'
        "[tool.uv.workspace]\n"
        f"members = {json.dumps(members)}\n",
        encoding="utf-8",
    )


def _write_member(root: Path, member: str, *, module: str = "runner.py", body: str) -> Path:
    """One workspace member's SHIPPED package: ``<root>/<member>/<member>/<module>``."""
    package = root / member / member
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    path = package / module
    path.write_text(body, encoding="utf-8")
    return path


def _shellout(binary: str) -> str:
    """A shipped module that execs ``binary`` through the plainest possible form."""
    return (
        "import subprocess\n"
        "\n"
        "\n"
        "def go() -> None:\n"
        f'    subprocess.run(["{binary}", "--version"], check=False)\n'
    )


class TestTheDerivedSetForThisRepo:
    """The golden read — and why a RED here is a feature, not a chore."""

    def test_the_derived_set_is_exactly_the_binaries_the_image_must_carry(self) -> None:
        derived = required_binaries(_REPO_ROOT)

        assert derived == _TODAYS_DERIVED_SET, (
            f"the SHIPPED code's external-binary set changed: {sorted(derived)!r}. This "
            f"set is what the deploy demands of the image (layers 2/3). If a new binary "
            f"appeared, it must be INSTALLED IN THE IMAGE (Containerfile) before this "
            f"pin is updated — the whole point of deriving it is that nobody has to "
            f"remember, and this RED is the reminder (findings #125/#131: the image had "
            f"no git, so the honesty line and every snapshot's git_ref were silently null)"
        )

    def test_the_scan_resolves_every_site_in_this_repo(self) -> None:
        # If this raises, some shipped call site's argv[0] is not a literal (or a shipped
        # module can spawn in a form the scan does not understand) — a HUMAN VERDICT is
        # owed, and the deploy gate must not proceed on a set it cannot trust.
        required_binaries(_REPO_ROOT)


class TestTheDerivationIsReal:
    """Kills the build that hardcodes the answer or the member list."""

    def test_the_members_come_from_the_workspace_not_a_hardcoded_list(
        self, tmp_path: Path
    ) -> None:
        # THREE members, THREE different binaries, none of them this repo's. A scan that
        # walks a hardcoded ["lorescribe", "loresigil", "loremaster"], or that only walks
        # ONE package, or that returns a hardcoded {"git"}, cannot pass this.
        _write_workspace(tmp_path, ["alpha", "beta", "gamma"])
        _write_member(tmp_path, "alpha", body=_shellout(_ALPHA_BINARY))
        _write_member(tmp_path, "beta", body=_shellout(_BETA_BINARY))
        _write_member(tmp_path, "gamma", body=_shellout(_GAMMA_BINARY))

        derived = required_binaries(tmp_path)

        assert derived == frozenset({_ALPHA_BINARY, _BETA_BINARY, _GAMMA_BINARY}), (
            "every SHIPPED workspace member must be scanned, and the binary set must be "
            "DERIVED from their source — not hardcoded (coverage is a checked variable)"
        )
        assert "git" not in derived

    def test_a_new_workspace_member_grows_the_required_set_by_itself(
        self, tmp_path: Path
    ) -> None:
        # THE POINT OF THE WHOLE INSTRUMENT. A member added to the image (the workspace)
        # must extend the required-binary set with NO edit to the deploy, the probe, or
        # any list. If this fails, someone has to remember — and this repo's history says
        # they will not.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", body=_shellout(_ALPHA_BINARY))
        assert required_binaries(tmp_path) == frozenset({_ALPHA_BINARY})

        _write_workspace(tmp_path, ["alpha", "delta"])
        _write_member(tmp_path, "delta", body=_shellout(_BETA_BINARY))

        assert required_binaries(tmp_path) == frozenset({_ALPHA_BINARY, _BETA_BINARY})

    def test_code_that_does_not_SHIP_is_not_required_of_the_image(
        self, tmp_path: Path
    ) -> None:
        # The other direction — an OVER-broad set is its own failure: it would make the
        # deploy demand binaries the image has no reason to carry (and this repo's test
        # trees + skill scripts shell out to plenty). Only the INSTALLED package of each
        # workspace member runs in the image.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", body=_shellout(_ALPHA_BINARY))
        # A test tree inside the member (copied into the image, never RUN there).
        tests = tmp_path / "alpha" / "tests"
        tests.mkdir(parents=True)
        (tests / "test_thing.py").write_text(_shellout(_UNSHIPPED_BINARY), encoding="utf-8")
        # A top-level directory that is NOT a workspace member (a script, a tool).
        _write_member(tmp_path, "toolbox", body=_shellout(_UNSHIPPED_BINARY))

        derived = required_binaries(tmp_path)

        assert derived == frozenset({_ALPHA_BINARY}), (
            f"only the SHIPPED package of each workspace member may contribute to the "
            f"required set — {_UNSHIPPED_BINARY!r} came from a test tree or a non-member "
            f"directory, neither of which runs in the image"
        )


class TestEverySpawnFormIsSeen:
    """Coverage as a CHECKED variable: the forms the scan must understand."""

    @pytest.mark.parametrize(
        ("form", "body"),
        [
            pytest.param(
                "subprocess.run",
                'import subprocess\nsubprocess.run(["rg", "-n"], check=False)\n',
                id="subprocess_run",
            ),
            pytest.param(
                "subprocess.Popen",
                'import subprocess\nsubprocess.Popen(["rg", "-n"])\n',
                id="subprocess_Popen",
            ),
            pytest.param(
                "subprocess.check_output",
                'import subprocess\nsubprocess.check_output(["rg", "-n"])\n',
                id="subprocess_check_output",
            ),
            pytest.param(
                "subprocess.call",
                'import subprocess\nsubprocess.call(["rg", "-n"])\n',
                id="subprocess_call",
            ),
            pytest.param(
                "os.execvp",
                'import os\nos.execvp("rg", ["rg", "-n"])\n',
                id="os_execvp",
            ),
            pytest.param(
                "os.system",
                'import os\nos.system("rg -n pattern")\n',
                id="os_system",
            ),
            pytest.param(
                "asyncio.create_subprocess_exec",
                "import asyncio\n\n\nasync def go() -> None:\n"
                '    await asyncio.create_subprocess_exec("rg", "-n")\n',
                id="asyncio_create_subprocess_exec",
            ),
        ],
    )
    def test_the_binary_is_derived_from_every_spawn_form(
        self, tmp_path: Path, form: str, body: str
    ) -> None:
        # A scan that only knows ``subprocess.run`` silently returns an EMPTY set for the
        # others — and an empty required set makes layer 2 pass vacuously over a container
        # missing the binary. That is the name-list losing again, one level down.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", body=body)

        assert required_binaries(tmp_path) == frozenset({_ALPHA_BINARY}), (
            f"the scan did not see a {form} call site — a spawn form it cannot read is a "
            f"binary the image will silently lack"
        )


class TestTheScanFailsLoud:
    """The two escapes. Both are a HUMAN VERDICT, never a silent shrink."""

    def test_an_unresolvable_argv0_fails_loud_naming_the_site(self, tmp_path: Path) -> None:
        _write_workspace(tmp_path, ["alpha"])
        path = _write_member(
            tmp_path,
            "alpha",
            module="dynamic.py",
            body=(
                "import subprocess\n"
                "\n"
                "\n"
                "def go(cmd: list[str]) -> None:\n"
                "    subprocess.run(cmd, check=False)\n"
            ),
        )

        with pytest.raises(UnresolvedExecSiteError) as raised:
            required_binaries(tmp_path)

        message = str(raised.value)
        assert "dynamic.py" in message, (
            "an exec site whose argv[0] is not a literal must be reported with its "
            f"LOCATION so a human can rule on it (site: {path})"
        )
        assert ":5" in message or "line 5" in message, (
            f"the raise must name the LINE of the unresolvable site, not just the file "
            f"(got: {message!r})"
        )

    def test_a_resolvable_site_in_the_same_shape_does_NOT_raise(self, tmp_path: Path) -> None:
        # THE POSITIVE CONTROL for the pin above: same module, same call, same everything
        # — only argv[0] is now a literal. If this raised too, the pin above would be
        # passing for the wrong reason (a scan that refuses everything is not a scan).
        _write_workspace(tmp_path, ["alpha"])
        _write_member(
            tmp_path,
            "alpha",
            module="dynamic.py",
            body=(
                "import subprocess\n"
                "\n"
                "\n"
                "def go() -> None:\n"
                f'    subprocess.run(["{_ALPHA_BINARY}"], check=False)\n'
            ),
        )

        assert required_binaries(tmp_path) == frozenset({_ALPHA_BINARY})

    def test_a_scan_over_NOTHING_fails_loud_rather_than_returning_an_empty_set(
        self, tmp_path: Path
    ) -> None:
        # THE VACUOUS-GATE PIN — found by running this contract against its own reference
        # build, where a mis-resolved repo root produced zero members and the deploy
        # cheerfully printed "container binaries OK ()" over a container with NOTHING in
        # it. An empty required set is not a permissive answer, it is a DEAD GATE: layer 2
        # iterates over nothing and passes, so a git-less image sails through exactly as
        # it did before this instrument existed.
        #
        # Note the discrimination: "the workspace declares no packages" (a broken scan)
        # must fail loud, while "the packages exist and exec nothing" is a legitimate
        # empty answer. Only the first is pinned here.
        _write_workspace(tmp_path, [])

        with pytest.raises(ShelloutScanError):
            required_binaries(tmp_path)

        # A root that is not a workspace at all (no pyproject) — same verdict.
        with pytest.raises(ShelloutScanError):
            required_binaries(tmp_path / "not-a-workspace")

    def test_shipped_packages_that_exec_NOTHING_are_a_legitimate_empty_answer(
        self, tmp_path: Path
    ) -> None:
        # THE POSITIVE CONTROL for the pin above: the scan must not simply refuse every
        # empty result — a member that shells out to nothing legitimately requires no
        # binary. Without this leg, "raise when empty" could be satisfied by a scan that
        # always raises.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(
            tmp_path, "alpha", body="def go() -> int:\n    return 1\n"
        )

        assert required_binaries(tmp_path) == frozenset()

    def test_a_module_that_can_spawn_but_shows_no_exec_site_fails_loud(
        self, tmp_path: Path
    ) -> None:
        # THE COVERAGE GUARD (the repo's instrument law, one level up from the name-list):
        # a shipped module that imports a process spawner but yields NO resolved exec site
        # means the scan does not understand what that module does. The honest answer is a
        # loud human verdict — never an empty set that makes the deploy gate green over a
        # binary the image lacks.
        #
        # Verified against the real tree before this pin was written: exactly ONE shipped
        # module imports subprocess (loremaster/loremaster/index/snapshots.py), and it has
        # one resolved site — so this guard is satisfiable today.
        _write_workspace(tmp_path, ["alpha"])
        # A perfectly resolvable site lives alongside it: a scan that answered {"rg"} and
        # shrugged at the opaque module would look like a working scan. It must not.
        _write_member(tmp_path, "alpha", body=_shellout(_ALPHA_BINARY))
        _write_member(
            tmp_path,
            "alpha",
            module="opaque.py",
            body=(
                "import subprocess\n"
                "\n"
                "SPAWNER = subprocess.Popen\n"
                "\n"
                "\n"
                "def go(argv: list[str]) -> None:\n"
                "    SPAWNER(argv)\n"
            ),
        )

        with pytest.raises(UnresolvedExecSiteError) as raised:
            required_binaries(tmp_path)

        assert "opaque.py" in str(raised.value), (
            "a shipped module that can spawn a process but shows the scan no resolvable "
            "exec site must FAIL LOUD (naming the module): a silently-empty answer there "
            "is exactly how a required binary goes missing from the image"
        )
