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
import re
from pathlib import Path
from typing import Any

import loremaster.shellout as shellout_module
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


# --------------------------------------------------------------------------- #
# FIX WAVE (packet 01, cold audit REPORT-pkt01-audit-1.md §D DEFECT-3/DEFECT-4, §R R3)
# --------------------------------------------------------------------------- #

# A plainly-resolvable exec site, for the CO-RESIDENT flavour of every shape below. Its
# presence is the whole trick: today's coverage guard is keyed per-MODULE
# (``resolved_sites == 0 and _can_spawn(tree)``), so ONE resolvable call disarms the check
# for the ENTIRE file — and every other exec site in it becomes invisible, silently.
_RESOLVABLE_SITE = (
    "import subprocess\n"
    "\n"
    "\n"
    "def resolvable() -> None:\n"
    f'    subprocess.run(["{_ALPHA_BINARY}", "-n"], check=False)\n'
    "\n"
    "\n"
)

# The Containerfile the image is actually built from — the artifact this whole instrument
# exists to gate. Read, never guessed.
_CONTAINERFILE = _REPO_ROOT / "Containerfile"

# A binary the image installs but NO gate protects must be DECLARED, with a reason, in the
# Containerfile itself. The declaration turns an ungated binary from a silent fact into a
# CHECKED variable — the same move the derived set makes for the gated ones.
#
#     # lore-ungated-binary: curl — reserved for a container healthcheck; no shipped code execs it
#
_UNGATED_MARKER = re.compile(
    r"^#\s*lore-ungated-binary:\s*(?P<name>[A-Za-z0-9._+-]+)\s*[—:-]\s*(?P<reason>\S.*)$"
)
# The identifiers by which a Containerfile comment CITES the layer-2 gate. A comment block
# that cites the gate is making a claim ABOUT the gate, and that claim is checkable.
_GATE_CITATIONS = ("shellout", "required_binaries", "layer 2", "layer-2")
_MIN_REASON_CHARS = 20


def _containerfile_text() -> str:
    return _CONTAINERFILE.read_text(encoding="utf-8")


def _apt_installed_binaries(text: str) -> set[str]:
    """The binaries the image apt-installs (the packages named on the ``apt-get install`` line).

    Deliberately parsed from the REAL Containerfile rather than restated here: a hand-kept
    copy of the install list is the very thing this file exists to abolish. (Package name ==
    binary name for the trivial packages the image installs; a package whose binary differs
    would need an explicit mapping, and the pins below would go RED and demand one — which
    is the instrument working.)
    """
    assert "apt-get install" in text, "the Containerfile no longer has an apt-get install line"
    tail = text.split("apt-get install", 1)[1]
    tail = tail.replace("\\\n", " ")  # join the shell line-continuations
    tail = tail.split("&&")[0]  # …but stop at the NEXT shell command (`&& rm -rf …`)
    tail = tail.split("\n")[0]  # …and never cross into a new RUN
    installed = {token for token in tail.split() if not token.startswith("-")}
    assert installed, (
        f"parsed NO packages from the Containerfile's apt-get install line — the parser is "
        f"broken, and every pin in this class would then pass VACUOUSLY over an image that "
        f"installs anything at all. (tail parsed: {tail!r})"
    )
    return installed


def _declared_ungated(text: str) -> dict[str, str]:
    """The ungated binaries the Containerfile explicitly DECLARES, name → reason."""
    declared: dict[str, str] = {}
    for line in text.splitlines():
        match = _UNGATED_MARKER.match(line.strip())
        if match is not None:
            declared[match.group("name")] = match.group("reason").strip()
    return declared


def _comment_blocks(text: str) -> list[str]:
    """Maximal runs of consecutive comment lines — one block per prose claim."""
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            current.append(line)
        elif current:
            blocks.append("\n".join(current))
            current = []
    if current:
        blocks.append("\n".join(current))
    return blocks


def _resolved_or_loud(
    root: Path, body: str, *, module: str = "runner.py"
) -> tuple[frozenset[str] | None, str]:
    """Run the derivation over a one-member workspace whose shipped module is ``body``.

    Returns ``(derived_set, "")`` when the scan VOUCHED for an answer, or
    ``(None, message)`` when it refused. Those are the only two outcomes the docstring of
    ``shellout.py`` permits; a third — a set that silently omits a real exec site — is the
    defect these pins exist to make impossible.
    """
    _write_workspace(root, ["alpha"])
    _write_member(root, "alpha", module=module, body=body)
    try:
        return required_binaries(root), ""
    except ShelloutScanError as raised:
        return None, str(raised)


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


# --------------------------------------------------------------------------- #
# FIX WAVE / F3 — DEFECT-3: the DERIVED set is a name-list wearing a derivation's clothes
# --------------------------------------------------------------------------- #
# Each row is (id, module body, the binary that exec site launches — or None when argv[0]
# is genuinely unresolvable and LOUD is the only correct fate). Every row appears TWICE:
# ALONE, and CO-RESIDENT with a plainly-resolvable ``subprocess.run(["rg"])`` site. The
# co-resident flavour is the killer: today's coverage guard is keyed per-MODULE, so that
# one resolvable call disarms the check for the whole file.
_EXEC_SHAPES: list[tuple[str, str, str | None]] = [
    (
        "aliased_import",
        'import subprocess as sp\n\n\ndef go() -> None:\n    sp.run(["fd", "."], check=False)\n',
        "fd",
    ),
    (
        # The alias is NOT one of the names anyone would think to enumerate. That is the
        # point: the forbidden set is unbounded, so a scan keyed on RECEIVER NAMES loses.
        "obscure_alias",
        "import subprocess as _zz_engine\n\n\ndef go() -> None:\n"
        '    _zz_engine.Popen(["fd", "."])\n',
        "fd",
    ),
    (
        "from_import",
        'from subprocess import run\n\n\ndef go() -> None:\n    run(["hg", "id"], check=False)\n',
        "hg",
    ),
    (
        "from_import_aliased",
        "from subprocess import run as launch\n\n\ndef go() -> None:\n"
        '    launch(["hg", "id"], check=False)\n',
        "hg",
    ),
    (
        # The audit's headline: `system("curl … | sh")` — a SHELL string — invisible.
        "from_os_import_system",
        'from os import system\n\n\ndef go() -> None:\n    system("hg id")\n',
        "hg",
    ),
    (
        "from_os_import_execvp",
        'from os import execvp\n\n\ndef go() -> None:\n    execvp("fd", ["fd", "."])\n',
        "fd",
    ),
    (
        "from_asyncio_import_create_subprocess_exec",
        "from asyncio import create_subprocess_exec\n\n\nasync def go() -> None:\n"
        '    await create_subprocess_exec("fd", ".")\n',
        "fd",
    ),
    (
        # argv[0] built at RUNTIME: no set can contain it, so LOUD is the ONLY honest fate.
        "runtime_argv_via_from_import",
        "from subprocess import run\n\n\ndef go(cmd: list[str]) -> None:\n"
        "    run(cmd, check=False)\n",
        None,
    ),
    (
        "runtime_argv_via_alias",
        "import subprocess as sp\n\n\ndef go(cmd: list[str]) -> None:\n"
        "    sp.run(cmd, check=False)\n",
        None,
    ),
]

def _shape_params() -> list[Any]:
    """Every shape TWICE: alone, and with a resolvable co-resident site beside it."""
    cases: list[Any] = []
    for shape_id, body, binary in _EXEC_SHAPES:
        cases.append(pytest.param(body, binary, False, id=shape_id))
        cases.append(
            pytest.param(
                _RESOLVABLE_SITE + body, binary, True, id=f"{shape_id}__with_a_resolvable_site"
            )
        )
    return cases


_SHAPE_PARAMS = _shape_params()


class TestEveryExecSiteIsResolvedOrLoud:
    """THE ∀-PROPERTY (DEFECT-3). Not "the scan knows these seven shapes" — that invariant
    is conditioned on the shapes we happened to think of, which is the same bug one level up
    (the quantifier law). The property is:

        for EVERY exec site in shipped code, either its binary is RESOLVED into the derived
        set, or the scan FAILS LOUD naming ``file:line``. There is no third outcome.

    The third outcome is what ships today. ``shellout.py``'s own docstring promises
    *"Coverage is a CHECKED variable, never a hope"* and *"A new shell-out grows the required
    set BY ITSELF"*. Both are FALSE: ``_exec_receiver`` keys on RECEIVER NAMES
    (``subprocess``/``os``/``asyncio``) and ``_can_spawn`` is a second, WEAKER name-list. The
    audit walked straight through it (positive control first — a plain
    ``subprocess.run(["git"…])`` derives ``['git']``):

        from os import system                    + a resolvable site → ['git']  SILENT MISS
        from os import system                    alone              → []        VACUOUS
        from asyncio import create_subprocess_exec alone            → []        VACUOUS
        import subprocess as sp                  + a resolvable site → ['git']  SILENT MISS
        from subprocess import run               + a resolvable site → ['git']  SILENT MISS

    Root cause: the coverage guard is keyed per-MODULE (``resolved_sites == 0 and
    _can_spawn(tree)``), so ONE resolvable call disarms the check for the whole file.

    This is THIS REPO'S OWN instrument lesson recurring INSIDE the fix that cites it —
    *"a gate keyed on 2 receiver names, defeated by six other doors"*. Today's answer is
    still right (``{git}`` really is the only exec site), so the artifact ships correct; the
    GUARANTEE is a hope. The next shell-out written from-import style reproduces #131 exactly,
    silently, with every gate green.

    Fixture discipline: never ``git``, and one alias (``_zz_engine``) that no name-list
    would ever contain.
    """

    @pytest.mark.parametrize(("body", "hidden_binary", "co_resident"), _SHAPE_PARAMS)
    def test_an_exec_site_is_resolved_into_the_set_or_the_scan_fails_loud(
        self, tmp_path: Path, body: str, hidden_binary: str | None, co_resident: bool
    ) -> None:
        derived, message = _resolved_or_loud(tmp_path, body)

        if derived is None:
            # FATE 2 — the scan refused. It must say WHERE, or a human cannot rule on it.
            assert "runner.py" in message, (
                f"the scan refused to vouch for the set but did not name the FILE — an "
                f"unactionable refusal. Got: {message!r}"
            )
            assert re.search(r":\d+|line \d+", message), (
                f"the scan refused but did not name the LINE of the site it could not "
                f"read. 'Somewhere in this module' is not a verdict a human can act on. "
                f"Got: {message!r}"
            )
            return

        # FATE 1 — the scan VOUCHED for a set. Then the site's binary is IN it, or the
        # scan just told the deploy an image is complete when it is not.
        assert hidden_binary is not None, (
            f"argv[0] here is built at RUNTIME — the scan CANNOT know what this launches, "
            f"so the only honest answer is a loud refusal. It returned {sorted(derived)!r} "
            f"instead, and the deploy will now trust that set to be complete"
        )
        assert hidden_binary in derived, (
            f"SILENT MISS: the shipped module execs {hidden_binary!r} and the derived set "
            f"is {sorted(derived)!r}. The scan neither saw the site nor admitted it could "
            f"not — the third outcome, which shellout.py's docstring says cannot happen "
            f"('Coverage is a CHECKED variable, never a hope'). The image will not carry "
            f"{hidden_binary!r}, every gate will stay green, and the shell-out is a silent "
            f"None in production — finding #131, reproduced exactly (DEFECT-3)"
        )

    @pytest.mark.parametrize(("body", "hidden_binary", "co_resident"), _SHAPE_PARAMS)
    def test_a_co_resident_resolvable_site_never_disarms_the_scan(
        self, tmp_path: Path, body: str, hidden_binary: str | None, co_resident: bool
    ) -> None:
        # THE PER-SITE PIN, stated separately because it is the ROOT CAUSE. Whatever the
        # scan's verdict on the hidden site, the resolvable co-resident site must ALSO be
        # accounted for — coverage is a property of every SITE, never of the module that
        # happens to contain one readable call.
        if not co_resident:
            pytest.skip("this row is the ALONE flavour; the co-resident pin is its twin")

        derived, message = _resolved_or_loud(tmp_path, body)

        if derived is None:
            assert "runner.py" in message
            return
        assert _ALPHA_BINARY in derived, (
            f"the co-resident resolvable site vanished too: {sorted(derived)!r}"
        )
        assert hidden_binary is not None, (
            f"the second site's argv[0] is built at RUNTIME and the scan vouched for "
            f"{sorted(derived)!r} anyway — the readable call beside it was enough to make "
            f"the scan stop asking. The guard is keyed per-MODULE; it must be per-SITE"
        )
        assert hidden_binary in derived, (
            f"one resolvable call ({_ALPHA_BINARY}) disarmed the coverage check for the "
            f"WHOLE FILE, and the second exec site ({hidden_binary!r}) was dropped in "
            f"silence — derived: {sorted(derived)!r}. The guard is keyed per-MODULE "
            f"(`resolved_sites == 0 and _can_spawn(tree)`); it must be keyed per-SITE"
        )

    def test_the_positive_control_a_plain_exec_site_still_resolves(
        self, tmp_path: Path
    ) -> None:
        # A PROBE NEEDS A CONTROL. Every pin above could be satisfied by a scan that
        # refuses EVERYTHING — an instrument that always fires discriminates nothing. The
        # plainest possible site must still resolve, silently and correctly.
        derived, message = _resolved_or_loud(tmp_path, _shellout(_ALPHA_BINARY))

        assert derived == frozenset({_ALPHA_BINARY}), (
            f"a plain `subprocess.run([...])` no longer resolves — the fix turned the scan "
            f"into a machine that refuses to vouch for anything, which gates nothing while "
            f"looking strict. (message: {message!r})"
        )

    def test_the_negative_control_a_module_with_no_spawner_stays_silent(
        self, tmp_path: Path
    ) -> None:
        # The OTHER control: a stricter scan must not start seeing spawners where there are
        # none. ``os`` and ``asyncio`` are imported all over shipped code for reasons that
        # have nothing to do with processes; flagging them would make the instrument
        # unusable and it would be turned off.
        body = (
            "import asyncio\n"
            "import os\n"
            "\n"
            "\n"
            "async def go() -> str:\n"
            "    await asyncio.sleep(0)\n"
            "    return os.getcwd()\n"
        )
        derived, message = _resolved_or_loud(tmp_path, body)

        assert derived == frozenset(), (
            f"a module that imports os/asyncio and spawns NOTHING was flagged as a spawn "
            f"site — the scan now cries wolf on every import in the tree (message: "
            f"{message!r})"
        )


# --------------------------------------------------------------------------- #
# FIX WAVE / F6 — R3: the empty set has THREE causes, and they are NOT the same fact
# --------------------------------------------------------------------------- #
class TestTheEmptySetHasDistinctCauses:
    """``shellout.py``'s docstring says *"An EMPTY answer is the dangerous one"*. The
    contract says ``test_shipped_packages_that_exec_NOTHING_are_a_legitimate_empty_answer``.
    ``_probe_container_binaries`` cheerfully prints ``container binaries OK ()``. Three
    artifacts, three different beliefs about the same value.

    THE RULING (contract author's, stated for the record — see the report's F6): **the
    OUTCOME is not the danger; the CAUSE is.** An empty set has three causes and they must
    not share a fate:

    * the scan found NO MODULES → dangerous → ``ShelloutScanError`` (a gate over nothing).
    * a module CAN spawn but the scan cannot read its sites → dangerous →
      ``UnresolvedExecSiteError`` (the F3 class: today this is the SILENT one).
    * the shipped packages genuinely exec nothing → LEGITIMATE → ``frozenset()``, and the
      deploy says so in words (``TestTheEmptySetIsReportedHonestly`` in the skill contract).

    The docstring is the artifact that is wrong. Prose that describes behaviour must be
    DERIVED from the behaviour, not restated beside it — and where it cannot be derived, it
    must at least not contradict the pins.
    """

    def test_no_modules_is_dangerous_and_raises(self, tmp_path: Path) -> None:
        _write_workspace(tmp_path, [])
        with pytest.raises(ShelloutScanError):
            required_binaries(tmp_path)

    def test_an_unreadable_spawn_site_is_dangerous_and_raises(self, tmp_path: Path) -> None:
        derived, message = _resolved_or_loud(
            tmp_path,
            "import subprocess as sp\n\n\ndef go(cmd: list[str]) -> None:\n"
            "    sp.run(cmd, check=False)\n",
        )
        assert derived is None, (
            f"a module whose exec site the scan cannot read returned a set "
            f"({sorted(derived or [])!r}) instead of refusing — the deploy now trusts a "
            f"required set that was never derived"
        )
        assert "runner.py" in message

    def test_packages_that_exec_nothing_are_a_LEGITIMATE_empty_answer(
        self, tmp_path: Path
    ) -> None:
        # The discrimination that makes the two pins above mean something: the scan must not
        # simply refuse every empty result. "Raise when empty" is satisfiable by a scan that
        # always raises — and that is not a derivation, it is a wall.
        derived, message = _resolved_or_loud(tmp_path, "def go() -> int:\n    return 1\n")

        assert derived == frozenset(), (
            f"a shipped package that execs nothing requires no binary — an empty set here "
            f"is the CORRECT answer, and the scan refused it ({message!r})"
        )

    def test_the_docstring_no_longer_calls_an_EMPTY_answer_the_dangerous_one(self) -> None:
        # An ANTI-REGRESSION pin, and it is honest about being one: a prose surface with no
        # derivation available gets a pin keyed on the false sentence it must lose. (The
        # general instrument for this class is the fate table above — this pin only stops
        # the specific contradiction from being re-typed.)
        prose = " ".join(
            (shellout_module.__doc__ or "").split()
            + (ShelloutScanError.__doc__ or "").split()
        ).lower()

        assert "empty answer is the dangerous one" not in prose, (
            "the docstring still says an EMPTY answer is THE dangerous one, while "
            "test_packages_that_exec_nothing_are_a_LEGITIMATE_empty_answer passes and the "
            "deploy prints OK over it. Name the CAUSE, not the outcome: a set derived from "
            "no modules, or from a module whose spawn sites could not be read, is the "
            "dangerous one — and both of those RAISE"
        )
        assert "legitimate" in prose or "legal" in prose, (
            "the docstring must say plainly that an empty set from packages which exec "
            "nothing is a legitimate answer — the fate table pins it, and the prose beside "
            "the code must not contradict the pins"
        )


# --------------------------------------------------------------------------- #
# FIX WAVE / F4 — DEFECT-4: the image's binary set is a CHECKED variable, not a comment
# --------------------------------------------------------------------------- #
class TestTheImageInstallsExactlyWhatTheScanGates:
    """``Containerfile:19-24`` claims the *"Layer 2 probe fails loud if **either binary**
    goes missing from the image"* — naming curl AND git. **False for curl.** The derived set
    contains only binaries the shipped PYTHON execs; curl is exec'd by no shipped code, so it
    can NEVER enter the set and NO gate can ever protect it. The audit verified it: delete
    curl from the apt line and every gate stays green.

    (Compounding it: curl's stated rationale — the container healthcheck — is stale. The
    image declares NO healthcheck at all, and ``--health-cmd`` appears nowhere in the skill.
    Reported, not fixed: not the contract author's call. See the report's F4.)

    The class of defect is this repo's most expensive one: **served English promising a
    mechanism that does not run.** The answer is not better prose — it is to make the claim a
    DERIVED, CHECKED variable:

    * every binary the shipped code execs must be INSTALLED (the gate that would have caught
      #131 in the repo suite, before any container existed);
    * every binary the image installs must be GATED — or explicitly DECLARED ungated, with a
      reason, in the Containerfile itself;
    * the comment block that CITES the gate may name only binaries the gate actually covers.

    Either honest fix passes: drop curl (the audit's verified path), or keep it and declare
    it. What is no longer possible is a file that installs an ungated binary and tells the
    reader it is gated.
    """

    def test_every_binary_the_shipped_code_execs_is_installed_by_the_image(self) -> None:
        # The #131 gate, at the REPO layer. The deploy probe catches a missing binary only
        # against a RUNNING container — i.e. after the image is built, pushed and launched.
        # This catches it the moment the shell-out lands.
        derived = required_binaries(_REPO_ROOT)
        installed = _apt_installed_binaries(_containerfile_text())

        assert derived <= installed, (
            f"the shipped code execs {sorted(derived - installed)!r}, which the image does "
            f"NOT install. That is finding #131 exactly: the seam shells out, the binary is "
            f"absent, the helper swallows the OSError, and the field is a silent null in "
            f"production while every test on a git-having host stays green. Add it to the "
            f"Containerfile's apt line"
        )

    def test_the_image_installs_no_binary_that_no_gate_protects(self) -> None:
        derived = required_binaries(_REPO_ROOT)
        text = _containerfile_text()
        installed = _apt_installed_binaries(text)
        declared = _declared_ungated(text)

        undeclared = installed - derived - set(declared)

        assert not undeclared, (
            f"the image installs {sorted(undeclared)!r}, which the derived set does not "
            f"contain — so NO gate protects them, and nothing in the tree says so. The "
            f"Containerfile meanwhile tells its reader the Layer 2 probe 'fails loud if "
            f"either binary goes missing'. It does not, and it cannot: only binaries the "
            f"shipped PYTHON execs can enter the derived set.\n"
            f"Two honest fixes, either is fine:\n"
            f"  (a) drop them from the apt line (the audit verified every gate stays green "
            f"without curl), or\n"
            f"  (b) DECLARE them, with a reason, in the Containerfile:\n"
            f"      # lore-ungated-binary: curl — reserved for a container healthcheck; no "
            f"shipped code execs it\n"
            f"An ungated binary is allowed. An ungated binary that the file CLAIMS is gated "
            f"is a false gate (DEFECT-4)"
        )

    def test_a_declared_ungated_binary_is_really_ungated_and_carries_a_reason(self) -> None:
        # The exemption seam is deny-by-default and evidence-backed, per repo law — never a
        # hole a builder can widen by typing a name into it. A declaration that names a
        # binary the scan DOES derive is a contradiction; a declaration with no reason is a
        # name-list with extra steps.
        derived = required_binaries(_REPO_ROOT)
        declared = _declared_ungated(_containerfile_text())

        for binary, reason in declared.items():
            assert binary not in derived, (
                f"{binary!r} is declared UNGATED but the shipped code execs it — it IS "
                f"gated (layer 2 requires it). Delete the declaration"
            )
            assert len(reason) >= _MIN_REASON_CHARS, (
                f"the ungated declaration for {binary!r} carries no real reason "
                f"({reason!r}). An exemption without evidence is the thing that blessed the "
                f"bootstrap DDL right before it lost 6-34% of concurrent first-connects"
            )

    def test_the_comment_that_explains_the_gate_names_only_gated_binaries(self) -> None:
        derived = required_binaries(_REPO_ROOT)
        text = _containerfile_text()
        installed = _apt_installed_binaries(text)
        ungated = installed - derived

        for block in _comment_blocks(text):
            lowered = block.lower()
            if not any(citation in lowered for citation in _GATE_CITATIONS):
                continue
            named = {
                binary
                for binary in ungated
                if re.search(rf"\b{re.escape(binary)}\b", lowered)
            }
            assert not named, (
                f"this comment block cites the layer-2 gate ({_GATE_CITATIONS}) and names "
                f"{sorted(named)!r} — binaries the gate CANNOT cover, because the derived "
                f"set only ever contains what the shipped PYTHON execs. A reader is being "
                f"told a check exists that does not. Explain an ungated binary somewhere "
                f"the gate is not the subject (a separate comment block), or stop "
                f"installing it.\nBlock:\n{block}"
            )
