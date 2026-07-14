"""Contract — findings #125/#131, LAYER 1: derive the binaries the IMAGE must carry.

The defect this closes is the one the contract-adversary found sitting UNDER the honesty
line: the deployed image had no ``git`` binary, so the CORRECT implementation of #125
served ``git_branch: null`` in the only environment the feature exists for (and #131 —
every production snapshot's ``git_ref`` was silently ``None`` for the same reason). Every
test in ``test_workspace_status.py`` runs on a host that HAS git, so no test there can
see it. The deploy therefore DERIVES the required binaries from our own source and
refuses an image that lacks one.

THIS FILE IS THE THIRD CONTRACT FOR THAT DERIVATION. The first two both lost the same way,
and the way they lost is the point:

* v1 keyed on RECEIVER NAMES (``subprocess`` / ``os`` / ``asyncio``) — defeated by
  ``import subprocess as sp``, ``from subprocess import run``, ``from os import system``.
* v2 keyed on the module's BINDINGS — closed those four and opened four more, three of
  them REGRESSIONS: ``self._runner = subprocess.run`` went from LOUD to SILENT,
  ``import os.path`` + ``os.system(...)`` went from RESOLVED to SILENT (v2 LOST a binary
  v1 FOUND), ``from subprocess import *`` went from LOUD to SILENT.
* v2's "∀ exec sites" pin was parameterised over a HAND-LISTED nine-shape corpus. **A
  universal quantifier evaluated over a name-list IS a name-list.**

The repo's standing law (CLAUDE.md, "the instrument lesson", six defeats): *"When you catch
yourself enumerating what is FORBIDDEN, you have already lost. The forbidden set is
unbounded; the SAFE set is small and enumerable — so ALLOWLIST THE SAFE."* A fourth
shape-list is not the answer. This contract pins a different SHAPE OF INSTRUMENT.

---------------------------------------------------------------------------------------
THE ARCHITECTURE THIS CONTRACT PINS — ONE SANCTIONED EXEC SEAM (operator, 2026-07-14)
---------------------------------------------------------------------------------------
No shipped module may reach a process spawner AT ALL, except an explicit, tiny allowlist.
Today that allowlist is exactly ONE file. Two sides, with opposite postures:

1. **The DENY side OVER-APPROXIMATES and fails LOUD.** Outside the allowlist the scan does
   not try to recognise HOW someone reaches a spawner — only that they MIGHT. Any doubt is
   a refusal naming ``file:line``. **A false positive is CHEAP and CORRECT**: a human
   either sanctions the module (deliberately, visibly) or rewrites it to use the seam.
   *Erring loud is the design, not a bug* — and it is what ends the shape game, because an
   evading shape in a non-sanctioned module still trips a detector that is not trying to be
   clever.
2. **The RESOLVE side is precise, and lives ONLY inside the allowlist.** We cannot demand a
   canonical, readable form of the whole codebase. We can demand it of ONE file. Inside the
   seam, ``argv[0]`` resolves to a literal or the scan FAILS LOUD naming ``file:line``.
3. **The allowlist is a CHECKED, VISIBLE artifact.** It cannot be grown silently, cannot be
   grown from INSIDE a module, and a file added to it must actually resolve — whereupon its
   binary enters the derived set and ``TestTheImageInstallsExactlyWhatTheScanGates`` demands
   the image install it. That chain is what makes a new shell-out impossible to ship
   silently.

**WHY THIS IS NOT v3 OF THE SAME MISTAKE.** v1/v2 keyed a name-list to decide *what to
RESOLVE* — so a shape the list missed produced a smaller set, SILENTLY, and the deploy
trusted it. Here the deny side's failure direction is INVERTED: a signal it half-sees is a
REFUSAL, and a shape it does not model at all still cannot resolve, because **there is no
resolution code path outside the seam at all** (``test_a_perfectly_resolvable_exec_site_
OUTSIDE_the_seam_fails_loud``). The set can no longer shrink in silence; it can only fail
loud or stay exactly what one reviewed file says it is.

The contract this file pins (the shape a builder must land):

* ``loremaster.shellout.SANCTIONED_EXEC_MODULES: frozenset[str]`` — repo-relative POSIX
  paths. The SAFE set. Today: exactly ``loremaster/loremaster/index/snapshots.py``.
* ``loremaster.shellout.required_binaries(repo_root, *, sanctioned=SANCTIONED_EXEC_MODULES)
  -> frozenset[str]`` — the derived set over the uv-workspace members the image installs.
  The ``sanctioned`` keyword exists so synthetic fixtures can declare their OWN seam and
  keep FOREIGN names throughout; the deploy calls it with NO keyword, and
  ``test_the_deploy_door_is_the_DEFAULT_allowlist`` pins that.
* ``loremaster.shellout.UnresolvedExecSiteError`` / ``ShelloutScanError`` — the refusals.
  Never a silent skip.

Fixture-value discipline (this repo's #1 defect class): every synthetic fixture below uses
member names and binaries UNLIKE this repo's own (``alpha``/``beta``/``gamma``,
``rg``/``fd``/``hg`` — never ``loremaster``, never ``git``), and the synthetic SEAM path is
foreign too (``alpha/alpha/seam.py``), so a build that hardcodes the member list, the
answer ``{"git"}``, or the real seam's path fails.

How to run:
    uv run pytest loremaster/tests/test_shellout_allowlist.py -n auto -q
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import loremaster.shellout as shellout_module
import pytest
from loremaster.shellout import (
    SANCTIONED_EXEC_MODULES,
    ShelloutScanError,
    UnresolvedExecSiteError,
    required_binaries,
)

# The REAL repo root, resolved from THIS FILE (never from the package's ``__file__``):
# the test tree always lives in the real checkout, even when the package under test is
# PYTHONPATH-shadowed by a scratch build.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# The one external binary lore's shipped code actually execs today, and the ONE file
# sanctioned to exec it. If either pin goes RED, the shipped code grew a NEW shell-out or a
# NEW exec seam: that RED is the instrument working — it is the moment a human must rule.
_TODAYS_DERIVED_SET = frozenset({"git"})
_TODAYS_SANCTIONED_SET = frozenset({"loremaster/loremaster/index/snapshots.py"})

# Deliberately foreign names — a hardcoded ["lorescribe", "loresigil", "loremaster"] member
# list, a hardcoded {"git"} answer, or a seam keyed on the real snapshots.py path must fail
# every synthetic fixture below.
_ALPHA_BINARY = "rg"
_BETA_BINARY = "fd"
_GAMMA_BINARY = "hg"
_UNSHIPPED_BINARY = "never-in-the-image"

# The synthetic SEAM: a foreign member, a foreign module name, a foreign path.
_SEAM = "alpha/alpha/seam.py"
_SEAM_ONLY = frozenset({_SEAM})
_NO_SEAM: frozenset[str] = frozenset()

# The Containerfile the image is actually built from — read, never guessed.
_CONTAINERFILE = _REPO_ROOT / "Containerfile"

_UNGATED_MARKER = re.compile(
    r"^#\s*lore-ungated-binary:\s*(?P<name>[A-Za-z0-9._+-]+)\s*[—:-]\s*(?P<reason>\S.*)$"
)
_GATE_CITATIONS = ("shellout", "required_binaries", "layer 2", "layer-2")
_MIN_REASON_CHARS = 20


# --------------------------------------------------------------------------- #
# Fixture plumbing
# --------------------------------------------------------------------------- #
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _shellout(binary: str) -> str:
    """A module that execs ``binary`` through the plainest, most resolvable form there is.

    Note what this is used for BOTH ways below: inside the seam it must RESOLVE, and outside
    the seam this very same text must FAIL LOUD. That pair IS the architecture.
    """
    return (
        "import subprocess\n"
        "\n"
        "\n"
        "def go() -> None:\n"
        f'    subprocess.run(["{binary}", "--version"], check=False)\n'
    )


def _derive(
    root: Path, *, sanctioned: frozenset[str] = _NO_SEAM
) -> tuple[frozenset[str] | None, str]:
    """``(derived_set, "")`` when the scan VOUCHED, or ``(None, message)`` when it refused.

    Those are the only two outcomes the architecture permits. A third — a set that silently
    omits a real exec site — is the defect every pin in this file exists to make impossible.
    """
    try:
        return required_binaries(root, sanctioned=sanctioned), ""
    except ShelloutScanError as raised:
        return None, str(raised)


def _one_member(root: Path, body: str, *, module: str = "runner.py") -> None:
    _write_workspace(root, ["alpha"])
    _write_member(root, "alpha", module=module, body=body)


# =========================================================================== #
# §A — THE ARCHITECTURE. These pins do not name a single spawn SHAPE.
# =========================================================================== #
class TestOneSanctionedExecSeam:
    """The invariant, stated so that no shape-list can satisfy it.

    Every other test file in this repo's history tried to enumerate the doors. These five
    pins never mention a door. They pin that **silence is a property of the PATH**, that the
    verdict outside the seam is **independent of the code shape and the receiver name**, and
    that **the seam cannot be widened from inside a module**. A build that satisfies these
    cannot be shape-keyed, because a shape-keyed build necessarily lets SOME shape resolve
    outside the seam — and the very first pin forbids that for the single most resolvable
    shape there is.
    """

    def test_a_perfectly_resolvable_exec_site_OUTSIDE_the_seam_fails_loud(
        self, tmp_path: Path
    ) -> None:
        """THE PIN. Everything else in this file is downstream of it.

        ``subprocess.run(["rg", "--version"])`` is the plainest, most readable exec site in
        Python. v1 resolved it. v2 resolved it. Both were RIGHT to, under their own design —
        and that is exactly why both lost: a scanner whose job is to RESOLVE arbitrary
        modules must model every way of reaching a spawner, and that set is unbounded.

        Under the sanctioned-seam architecture there is **no resolution code path outside
        the seam at all**. This module is not sanctioned, so the answer is not ``{"rg"}`` —
        it is a REFUSAL naming ``file:line``. A human then either sanctions the module or
        routes it through the seam. Both are visible, reviewed acts.

        A build that keeps a general-purpose resolver and merely bolts an allowlist on top
        passes every other pin in this class and dies here.
        """
        _one_member(tmp_path, _shellout(_ALPHA_BINARY))

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived is None, (
            f"a shipped module that is NOT a sanctioned exec seam reached a process spawner "
            f"and the scan RESOLVED it into {sorted(derived or [])!r} instead of refusing. "
            f"That is a general-purpose resolver — the design that lost twice. It must model "
            f"every way of reaching a spawner to stay honest, and it cannot: the shapes it "
            f"does not model shrink the set SILENTLY, which is finding #131 exactly. Outside "
            f"the ONE sanctioned seam the only legal answers are 'no spawner here' and a "
            f"LOUD refusal"
        )
        assert "runner.py" in message and re.search(r":\d+|line \d+", message), (
            f"the refusal must name file:line — a human cannot rule on 'somewhere in the "
            f"tree'. Got: {message!r}"
        )

    def test_silence_is_a_property_of_the_PATH_not_of_the_code_shape(
        self, tmp_path: Path
    ) -> None:
        """The architecture in one assertion: **the same bytes, two paths, two fates.**

        The module body is IDENTICAL in both legs — byte for byte, the same string object.
        Only its PATH differs. At the sanctioned path it resolves; anywhere else it is a
        loud refusal.

        This is the pin a shape-keyed build cannot fake. Any scanner that decides by reading
        the CODE gives the same verdict twice (it sees the same code!). Only a scanner that
        decides by the PATH — i.e. one that consults the allowlist BEFORE it consults the
        source — can pass. And it kills two specific wrong builds outright: an allowlist
        keyed on the module's BASENAME (``seam.py`` anywhere), and one keyed on a
        substring/suffix match rather than the exact repo-relative path.
        """
        body = _shellout(_ALPHA_BINARY)

        sanctioned_root = tmp_path / "sanctioned"
        _write_workspace(sanctioned_root, ["alpha"])
        _write_member(sanctioned_root, "alpha", module="seam.py", body=body)

        derived, message = _derive(sanctioned_root, sanctioned=_SEAM_ONLY)
        assert derived == frozenset({_ALPHA_BINARY}), (
            f"the SANCTIONED seam must resolve its exec site into the derived set — the "
            f"deploy has to know the image needs {_ALPHA_BINARY!r}. Got: {derived!r} / "
            f"{message!r}"
        )

        # Same bytes. Same member. A DIFFERENT path — and a different fate.
        elsewhere_root = tmp_path / "elsewhere"
        _write_workspace(elsewhere_root, ["alpha"])
        _write_member(elsewhere_root, "alpha", module="not_the_seam.py", body=body)

        derived, message = _derive(elsewhere_root, sanctioned=_SEAM_ONLY)
        assert derived is None, (
            f"BYTE-IDENTICAL code resolved at a path that is NOT the sanctioned seam "
            f"({sorted(derived or [])!r}). Silence must be a property of the PATH — a "
            f"reviewed, allowlisted file — never of the code's shape. A scanner that decides "
            f"by reading the source cannot tell these two files apart, and that is precisely "
            f"the scanner this architecture replaces"
        )
        assert "not_the_seam.py" in message, (
            f"the refusal must name the offending file. Got: {message!r}"
        )

    @pytest.mark.parametrize(
        ("shape_id", "body"),
        [
            # The SAME capability signal (subprocess enters the module), attached to bodies
            # with nothing structurally in common. The verdict must not move.
            pytest.param("never_called_at_all", "import subprocess\n", id="never_called"),
            pytest.param(
                "called_in_a_lambda",
                "import subprocess\n\nlaunch = lambda: subprocess.run(['x'])\n",
                id="lambda",
            ),
            pytest.param(
                "hidden_in_a_class_body",
                "import subprocess\n\n\nclass C:\n    r = subprocess.run\n",
                id="class_attr",
            ),
            pytest.param(
                "behind_a_type_checking_guard",
                "from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    import subprocess\n",
                id="type_checking",
            ),
            pytest.param(
                "inside_a_nested_function",
                "def outer():\n    def inner():\n        import subprocess\n\n        "
                "return subprocess\n\n    return inner\n",
                id="nested_def",
            ),
            pytest.param(
                "in_an_except_handler",
                "try:\n    pass\nexcept Exception:\n    import subprocess\n",
                id="except_body",
            ),
            pytest.param(
                "as_a_comprehension_element",
                "import subprocess\n\nRS = [subprocess.run for _ in range(3)]\n",
                id="comprehension",
            ),
            pytest.param(
                "decorating_something",
                "import subprocess\n\n\n@subprocess.run\ndef go():\n    pass\n",
                id="decorator",
            ),
        ],
    )
    def test_the_verdict_does_not_depend_on_the_CALL_SHAPE(
        self, tmp_path: Path, shape_id: str, body: str
    ) -> None:
        """THE ∀-PIN, done properly this time.

        v2's ∀-pin ranged over a hand-listed corpus of nine CALL SHAPES — so it could only
        ever see the shapes its author thought of, which is the quantifier law biting the
        test that cites it. **This pin quantifies over the wrong thing on purpose.**

        It holds the CAPABILITY fixed (``subprocess`` enters the module) and varies the body
        wildly — never called, called from a lambda, stashed on a class, hidden behind
        ``TYPE_CHECKING``, buried in a nested ``def``, in an ``except`` body, built by a
        comprehension, used as a DECORATOR. These bodies have nothing in common with each
        other and several are absurd. **The verdict must be the same for all of them**,
        because outside the seam the verdict is not a function of the body AT ALL.

        That property — *the body cannot change the answer* — is what a shape-list can never
        have, and it is checkable without enumerating a single door. A build that must
        RECOGNISE the call to refuse it fails the rows where there is no call.
        """
        _one_member(tmp_path, body)

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived is None, (
            f"the {shape_id!r} body brought a process spawner into a NON-sanctioned shipped "
            f"module and the scan vouched for {sorted(derived or [])!r} anyway. Outside the "
            f"seam the verdict must be a function of the CAPABILITY (a spawner reached this "
            f"module), never of the SHAPE of the call — a scan that has to recognise the "
            f"call in order to refuse it is a shape-list, and the next shape nobody listed "
            f"walks straight through it (v1 and v2, both)"
        )
        assert "runner.py" in message, f"the refusal must name the file. Got: {message!r}"

    @pytest.mark.parametrize(
        "receiver",
        [
            # Identifiers no name-list would ever contain. The point is not that these six
            # are special — it is that the checker CANNOT SEE the receiver, so the space they
            # are drawn from is irrelevant. Pick any others; the verdict cannot move.
            "_zz_engine", "ᴏs", "O0O0O", "helper", "self._runtime", "𝓍",
        ],
    )
    def test_the_verdict_does_not_depend_on_the_RECEIVER_NAME(
        self, tmp_path: Path, receiver: str
    ) -> None:
        """RECEIVER-BLINDNESS — the exact axis on which v1 died, closed by construction.

        v1 keyed on the receiver names ``subprocess`` / ``os`` / ``asyncio``, and the repo's
        instrument table records the result: *"a gate keyed on 2 receiver names, defeated by
        six other doors."* The forbidden receiver set is unbounded — you cannot enumerate the
        names a future author might bind a spawner to.

        So do not look at the receiver. ``<anything>.system("rg -n x")`` is a refusal on the
        strength of the ATTRIBUTE alone — ``system`` is in the stdlib's CLOSED, DOCUMENTED
        process-spawn API, which is a bounded set in a way that "every way to bind a name"
        never will be. That is the safe-set inversion, applied one level down.

        Yes, this over-approximates: an innocent ``platform.system()`` in a shipped module
        would be refused too. **That is the design.** A false positive costs one human ruling;
        a false negative cost us three months of null ``git_ref`` in production.
        """
        _one_member(tmp_path, f'{receiver}.system("{_ALPHA_BINARY} -n x")\n')

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived is None, (
            f"a shipped module reached a process-spawn primitive through the receiver "
            f"{receiver!r} and the scan vouched for {sorted(derived or [])!r}. The receiver "
            f"name must not enter the verdict at ALL — key on the CLOSED spawn API, never on "
            f"the unbounded set of names someone might bind it to (the v1 defeat, verbatim)"
        )
        assert "runner.py" in message, f"the refusal must name the file. Got: {message!r}"

    def test_a_module_cannot_SANCTION_ITSELF(self, tmp_path: Path) -> None:
        """The allowlist must not be growable from inside the code it governs.

        The obvious "convenient" design — a magic comment or a module-level flag that opts a
        file out (``# lore: allow-exec``, ``__lore_exec_seam__ = True``, a ``# noqa``) — makes
        the safe set writable by the very diff that needs auditing. A builder adding a
        shell-out could then silence the gate in the same commit, and the required-binary set
        would grow with NO reviewed change to any allowlist and NO new entry in the image.
        That is #131 with extra steps.

        Every plausible in-file exemption marker is thrown at the scan at once. All of them
        must be inert: the exemption lives in the ALLOWLIST, and nowhere else.
        """
        _one_member(
            tmp_path,
            "# lore: allow-exec\n"
            "# lore-exec-seam: yes\n"
            "# lore-sanctioned-exec: this module may spawn\n"
            "# shellout: ignore\n"
            "# noqa: S603\n"
            "__lore_exec_seam__ = True\n"
            "SANCTIONED = True\n"
            "\n" + _shellout(_ALPHA_BINARY),
        )

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived is None, (
            f"a shipped module talked its way out of the gate with an in-file marker and the "
            f"scan resolved it ({sorted(derived or [])!r}). The safe set must be a CHECKED, "
            f"EXTERNAL artifact that a reviewer sees change — never a pragma the same diff "
            f"can add beside the shell-out it exists to hide"
        )
        assert "runner.py" in message, f"the refusal must name the file. Got: {message!r}"


class TestTheAllowlistIsACheckedArtifact:
    """The safe set is small, enumerable, real, and NEEDED. It cannot rot or bloat quietly."""

    def test_todays_sanctioned_set_is_exactly_one_file(self) -> None:
        # THE GOLDEN PIN on the safe set. Growing the allowlist is the single most
        # security-relevant edit anyone can make to this instrument, so it is a deliberate
        # RED: a human must come here, read the architecture above, and change this line.
        assert SANCTIONED_EXEC_MODULES == _TODAYS_SANCTIONED_SET, (
            f"the sanctioned-exec allowlist changed: {sorted(SANCTIONED_EXEC_MODULES)!r}. "
            f"This set is the ENTIRE safe set — every other shipped module is denied a "
            f"process spawner outright. A new entry means a new module may exec: confirm its "
            f"argv[0] resolves, confirm the binary is INSTALLED IN THE IMAGE (Containerfile), "
            f"and only then update this pin. The RED is the review"
        )

    def test_the_deploy_door_is_the_DEFAULT_allowlist(self) -> None:
        # The ``sanctioned`` keyword exists for the synthetic fixtures in this file. The
        # PRODUCTION caller (skills/lore-deploy: required_container_binaries → a subprocess
        # into the loremaster interpreter → required_binaries(Path(...))) passes NO keyword.
        # If the default were anything other than the checked constant — or if the tests
        # exercised a door production never uses — every pin in this file would be theatre.
        derived = required_binaries(_REPO_ROOT)

        assert derived == required_binaries(_REPO_ROOT, sanctioned=SANCTIONED_EXEC_MODULES), (
            "the default value of `sanctioned` must BE the checked constant — the deploy "
            "calls required_binaries() with no keyword, so a different default would mean "
            "production and every test in this file walk through different doors"
        )
        assert derived == _TODAYS_DERIVED_SET

    def test_a_sanctioned_path_that_does_not_exist_fails_loud(self, tmp_path: Path) -> None:
        # A stale allowlist entry is a dead exemption: the file was renamed or deleted, and
        # nothing noticed. Left alone it rots into a hole — the day someone re-creates a file
        # at that path, it is silently exempt. Refuse it.
        _one_member(tmp_path, "def go() -> int:\n    return 1\n")

        derived, message = _derive(tmp_path, sanctioned=frozenset({"alpha/alpha/ghost.py"}))

        assert derived is None, (
            "the allowlist sanctions a path that does not exist and the scan shrugged. A "
            "stale exemption is a hole waiting for a file to be created at that path"
        )
        assert "ghost.py" in message, f"the refusal must name the stale entry. Got: {message!r}"

    def test_a_sanctioned_module_that_EXECS_NOTHING_fails_loud(self, tmp_path: Path) -> None:
        # Deny-by-default means every exemption must be EVIDENCE-BACKED (repo law: an
        # exemption blessed on opinion is what lost 6-34% of concurrent first-connects). An
        # allowlisted file that spawns nothing is an exemption nobody needs — and an open
        # door for the next shell-out to walk through unreviewed.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="seam.py", body="def go() -> int:\n    return 1\n")

        derived, message = _derive(tmp_path, sanctioned=_SEAM_ONLY)

        assert derived is None, (
            "a module is SANCTIONED to exec and execs nothing — an exemption with no reason "
            "to exist. It must be removed from the allowlist, not left as an unwatched door "
            "for the next shell-out to be written behind"
        )
        assert "seam.py" in message, f"the refusal must name the needless exemption. {message!r}"

    def test_sanctioning_a_module_GROWS_the_required_set_by_itself(self, tmp_path: Path) -> None:
        # THE CHAIN THAT MAKES A SILENT SHELL-OUT IMPOSSIBLE, end to end:
        #   a new exec site  →  refused (loud)                          [§A]
        #   → a human sanctions the file  →  its binary enters the set  [here]
        #   → the image must install it                                 [TestTheImageInstalls…]
        # Nobody has to REMEMBER anything. Every link is a gate, and the middle link is a
        # reviewed diff to the allowlist.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="seam.py", body=_shellout(_BETA_BINARY))

        refused, _ = _derive(tmp_path, sanctioned=_NO_SEAM)
        assert refused is None, "an unsanctioned exec site must be refused before it is blessed"

        derived, message = _derive(tmp_path, sanctioned=_SEAM_ONLY)
        assert derived == frozenset({_BETA_BINARY}), (
            f"sanctioning the seam must put its binary into the derived set with NO edit to "
            f"any other list — that is what the deploy then demands of the image. Got "
            f"{derived!r} / {message!r}"
        )


# =========================================================================== #
# §B — THE DENY SIDE. A SMOKE TEST, and it says so.
# =========================================================================== #
class TestHostileShapesFailLoud:
    """**THIS IS A SMOKE TEST, NOT THE INVARIANT.** Read §A for the invariant.

    A corpus of shapes is exactly what v2 mistook for a universal quantifier. It is kept here
    for one honest reason: it is a cheap regression net over doors we have *actually seen* an
    author (or an auditor) walk through. It cannot certify the absence of a door — only §A's
    body-independence and path-fate pins can approach that, and even they are bounded (see
    ``test_a_THIRD_PARTY_dependency_that_spawns_is_OUT_OF_REACH`` — the honest hole).

    Every shape here is one **I invented**, not one from the audit's table — the audit's four
    (``self._runner = subprocess.run``, ``import os.path`` → ``os.system``,
    ``from subprocess import *``, ``importlib.import_module``) are all subsumed by §A, and a
    corpus that only replays the last defeat is how you lose to the next one.
    """

    @pytest.mark.parametrize(
        ("door", "body"),
        [
            pytest.param("builtin __import__", '__import__("subprocess").run(["rg"])\n', id="dunder_import"),
            pytest.param(
                "importlib aliased AT the import",
                'from importlib import import_module as grab\n\ngrab("subprocess").Popen(["rg"])\n',
                id="importlib_aliased",
            ),
            pytest.param(
                "a spawner stashed on a class",
                "import os\n\n\nclass Shell:\n    launcher = os.system\n",
                id="class_attr_launcher",
            ),
            pytest.param("exec() of a source string", 'exec("import subprocess")\n', id="exec_source"),
            pytest.param(
                "getattr on an imported module, name COMPUTED",
                'import os\n\nspawn = getattr(os, "".join(["sys", "tem"]))\n',
                id="computed_getattr",
            ),
            pytest.param(
                "vars() of an imported module",
                'import os\n\nvars(os)["system"]("rg -n x")\n',
                id="vars_of_module",
            ),
            pytest.param(
                "the module's __dict__",
                'import os\n\nos.__dict__["system"]("rg -n x")\n',
                id="module_dunder_dict",
            ),
            pytest.param(
                "the sys.modules registry",
                'import sys\n\nsys.modules["subprocess"].run(["rg"])\n',
                id="sys_modules",
            ),
            pytest.param(
                "an import INSIDE a function",
                'def go():\n    import subprocess\n\n    subprocess.run(["rg"])\n',
                id="function_local_import",
            ),
            pytest.param(
                "a try/except-guarded import",
                "try:\n    import subprocess\nexcept ImportError:\n    subprocess = None\n",
                id="guarded_import",
            ),
            pytest.param(
                "a dotted alias of asyncio.subprocess",
                "import asyncio.subprocess as aps\n\n\nasync def go():\n"
                '    await aps.create_subprocess_exec("rg")\n',
                id="asyncio_dotted_alias",
            ),
            pytest.param(
                "a walrus around __import__",
                'def go():\n    (sp := __import__("subprocess")).run(["rg"])\n',
                id="walrus_import",
            ),
            pytest.param(
                "a runtime-concatenated module name",
                'import importlib\n\n\ndef go():\n'
                '    importlib.import_module("sub" + "process").run(["rg"])\n',
                id="concat_module_name",
            ),
            pytest.param(
                "os.spawnlp", 'import os\n\nos.spawnlp(os.P_NOWAIT, "rg", "rg")\n', id="os_spawnlp"
            ),
            pytest.param("pty.spawn", 'import pty\n\npty.spawn(["rg"])\n', id="pty_spawn"),
            pytest.param(
                "a subclass of Popen",
                "import subprocess\n\n\nclass Runner(subprocess.Popen):\n    pass\n",
                id="popen_subclass",
            ),
            pytest.param(
                "a spawner in a dict registry",
                'import os\n\nSPAWNERS = {"go": os.popen}\n',
                id="dict_registry",
            ),
            pytest.param(
                "a star-import of os (which re-exports system)",
                'from os import *\n\n\ndef go():\n    system("rg -n x")\n',
                id="star_import_os",
            ),
            pytest.param("multiprocessing", "import multiprocessing\n", id="multiprocessing"),
            pytest.param(
                "ctypes (libc.system is a spawner too)",
                'import ctypes\n\nctypes.CDLL(None).system(b"rg -n x")\n',
                id="ctypes_libc",
            ),
            pytest.param(
                "the receiver is self, not a module",
                'class C:\n    def go(self):\n        self.os.system("rg -n x")\n',
                id="receiver_is_self",
            ),
        ],
    )
    def test_a_hostile_shape_outside_the_seam_fails_loud(
        self, tmp_path: Path, door: str, body: str
    ) -> None:
        _one_member(tmp_path, body)

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived is None, (
            f"{door} reached a process spawner from a NON-sanctioned shipped module and the "
            f"scan vouched for {sorted(derived or [])!r}. The deploy will now trust that set "
            f"to be complete, the image will not carry what this module launches, and the "
            f"shell-out is a silent None in production — finding #131, reproduced"
        )
        assert "runner.py" in message and re.search(r":\d+|line \d+", message), (
            f"the refusal must name file:line so a human can rule on it. Got: {message!r}"
        )

    @pytest.mark.parametrize(
        ("what", "body"),
        [
            pytest.param(
                "ordinary os use (path, environ) — imported by half the tree",
                'import os\nfrom pathlib import Path\n\n\ndef go() -> str:\n'
                '    return os.environ.get("HOME", "") + os.path.sep + str(Path.cwd())\n',
                id="os_path_and_environ",
            ),
            pytest.param(
                "ordinary asyncio use",
                "import asyncio\n\n\nasync def go() -> None:\n    await asyncio.sleep(0)\n"
                "    await asyncio.to_thread(print, 'x')\n",
                id="asyncio_sleep_and_to_thread",
            ),
            pytest.param(
                "getattr on a NON-module (loremaster/config.py:310 does exactly this)",
                "class C:\n    def go(self, field: str) -> object:\n"
                "        return getattr(self, field)\n",
                id="getattr_on_self",
            ),
            pytest.param(
                "importlib.resources / importlib.metadata — NOT the import machinery",
                "import importlib.metadata\nfrom importlib import resources\n\n\n"
                'def go() -> str:\n    return importlib.metadata.version("x")\n',
                id="importlib_resources_and_metadata",
            ),
            pytest.param(
                "re.compile — an attribute named `compile`, which is not a spawner",
                'import re\n\n_RE = re.compile(r"x")\n',
                id="re_compile",
            ),
        ],
    )
    def test_the_NEGATIVE_CONTROL_ordinary_code_stays_silent(
        self, tmp_path: Path, what: str, body: str
    ) -> None:
        """A PROBE NEEDS A CONTROL — and an over-approximating deny side needs it MOST.

        Every pin in §A and §B above is satisfied by a scan that refuses EVERYTHING. That is
        not an instrument, it is a wall, and a wall gets switched off within the week. These
        five bodies are drawn from patterns that are ACTUALLY IN the shipped tree today
        (``os.environ``/``os.path`` everywhere, ``asyncio.to_thread`` in server.py,
        ``getattr(self, field)`` at config.py:310, ``importlib.metadata`` at server.py:43,
        ``re.compile`` in a dozen modules). Each must pass in silence.

        The reference build was run against all 78 shipped modules: **zero refusals.** If
        this class goes RED the deny side has become unusable, and an unusable gate is a
        deleted gate.
        """
        _one_member(tmp_path, body)

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived == frozenset(), (
            f"{what} was refused by the deny side ({message!r}). This pattern is all over "
            f"the shipped tree — a gate that cries wolf on it will be turned off, and then "
            f"it gates nothing at all. Over-approximate, but not into uselessness"
        )

    def test_a_THIRD_PARTY_dependency_that_spawns_is_OUT_OF_REACH(self, tmp_path: Path) -> None:
        """THE HONEST HOLE, pinned as a KNOWN BOUND rather than left to be rediscovered.

        A dependency that execs a binary on our behalf (``plumbum``, ``pexpect``,
        ``GitPython``, ``sh``) is INVISIBLE to any AST scan of OUR source: we see
        ``import plumbum``, and nothing in our tree names a spawner. The image could then
        lack a binary the *dependency* needs — #131's exact shape, one layer out.

        This is not a regression (v1 and v2 missed it too) and it is not closable by a source
        scan of our own code; closing it means scanning site-packages, which would make the
        deploy demand every binary every dependency can reach. **It is ledgered, not fixed** —
        and this pin exists so the bound is a CHECKED, VISIBLE fact rather than a surprise in
        the next audit. If a future build DOES close it, this pin goes RED and should be
        deleted with a cheer.

        Mitigation today: we ship no such dependency (verified — the only exec site in all
        three shipped packages is the sanctioned seam).
        """
        _one_member(tmp_path, 'import plumbum\n\nplumbum.local["rg"]()\n')

        derived, _ = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived == frozenset(), (
            "a third-party spawner is now DETECTED — the known bound has been closed. Good: "
            "delete this pin, and say so in the report"
        )


# =========================================================================== #
# §C — THE RESOLVE SIDE. Precise, and only inside the seam.
# =========================================================================== #
class TestInsideTheSeamTheFormIsCanonical:
    """We cannot demand a readable form of the whole codebase. We CAN demand it of one file.

    Inside the seam every reference to a spawner must be a direct call with a literal
    ``argv[0]``. Anything else — a spawner stashed on ``self``, a module constant holding
    ``Popen``, a ``functools.partial``, an alias, a from-import — is a LOUD refusal. This is
    also where audit residual **RA1 dies by construction**: v2's ``_learn_assignment``
    consumed ``node.value`` even for non-Name targets, which actively SUPPRESSED the
    fail-loud reference check and turned ``self._runner = subprocess.run`` (the most idiomatic
    shape of all — dependency injection) from LOUD into SILENT. There is no assignment
    learning here at all, so there is nothing to suppress.
    """

    @pytest.mark.parametrize(
        ("hazard", "body"),
        [
            pytest.param(
                "the spawner stashed on self (RA1 — v2's silent regression)",
                "import subprocess\n\n\nclass C:\n    def __init__(self) -> None:\n"
                "        self._runner = subprocess.run\n",
                id="RA1_self_runner",
            ),
            pytest.param(
                "a module constant holding the spawner",
                "import subprocess\n\nSPAWNER = subprocess.Popen\n\n\n"
                "def go(argv: list[str]) -> None:\n    SPAWNER(argv)\n",
                id="module_constant",
            ),
            pytest.param(
                "functools.partial of the spawner",
                'import functools\nimport subprocess\n\n'
                'launch = functools.partial(subprocess.run, ["rg"])\n',
                id="functools_partial",
            ),
            pytest.param(
                "argv[0] built at runtime",
                "import subprocess\n\n\ndef go(cmd: list[str]) -> None:\n"
                "    subprocess.run(cmd, check=False)\n",
                id="runtime_argv",
            ),
            pytest.param(
                "argv[0] is an f-string",
                "import subprocess\n\n\ndef go(b: str) -> None:\n"
                '    subprocess.run([f"{b}", "-v"], check=False)\n',
                id="fstring_argv0",
            ),
            pytest.param(
                "an EMPTY argv",
                "import subprocess\n\nsubprocess.run([], check=False)\n",
                id="empty_argv",
            ),
            pytest.param(
                "an ALIASED import, even in the seam",
                'import subprocess as sp\n\nsp.run(["rg"], check=False)\n',
                id="aliased_import_in_seam",
            ),
            pytest.param(
                "a from-import, even in the seam",
                'from subprocess import run\n\nrun(["rg"], check=False)\n',
                id="from_import_in_seam",
            ),
            pytest.param(
                "the module handed to a caller",
                "import subprocess\n\n\ndef go(f: object) -> None:\n    f(subprocess)\n",
                id="module_handed_away",
            ),
        ],
    )
    def test_an_unreadable_form_inside_the_seam_fails_loud(
        self, tmp_path: Path, hazard: str, body: str
    ) -> None:
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="seam.py", body=body)

        derived, message = _derive(tmp_path, sanctioned=_SEAM_ONLY)

        assert derived is None, (
            f"inside the sanctioned seam, {hazard} produced {sorted(derived or [])!r} instead "
            f"of a refusal. The seam is the ONE file whose exec sites the deploy trusts to be "
            f"complete — an argv it cannot read there is a required binary it will not demand, "
            f"and the image ships without it (#131). We can demand a canonical form of ONE "
            f"file; that is the entire reason the allowlist is tiny"
        )
        assert "seam.py" in message and re.search(r":\d+|line \d+", message), (
            f"the refusal must name file:line. Got: {message!r}"
        )

    @pytest.mark.parametrize(
        ("what", "body", "expected"),
        [
            pytest.param(
                "the plainest possible site",
                'import subprocess\n\nsubprocess.run(["rg", "-n"], check=False)\n',
                {_ALPHA_BINARY},
                id="plain_run",
            ),
            pytest.param(
                # THE REAL SHAPE of snapshots.py:119 — `except (OSError, subprocess.SubprocessError)`.
                # `SubprocessError` is an attribute of the spawner module that is NOT a spawn
                # call. A resolver that refuses every mention of `subprocess` would refuse the
                # ONE file this whole architecture is built around. Ask how I know.
                "a non-spawn attribute of the spawner module (the REAL seam's shape)",
                "import subprocess\n\n\ndef go() -> None:\n    try:\n"
                '        subprocess.run(["rg", "-n"], check=False)\n'
                "    except (OSError, subprocess.SubprocessError):\n        pass\n",
                {_ALPHA_BINARY},
                id="subprocess_SubprocessError",
            ),
            pytest.param(
                "a spawner CONSTANT (subprocess.PIPE) beside a real call",
                'import subprocess\n\nsubprocess.Popen(["rg"], stdout=subprocess.PIPE)\n',
                {_ALPHA_BINARY},
                id="subprocess_PIPE",
            ),
            pytest.param(
                "two different binaries in one seam",
                'import subprocess\n\nsubprocess.run(["rg"], check=False)\n'
                'subprocess.run(["hg", "id"], check=False)\n',
                {_ALPHA_BINARY, _GAMMA_BINARY},
                id="two_binaries",
            ),
            pytest.param(
                "os.system with a SHELL STRING (argv[0] is the first word)",
                'import os\n\nos.system("fd -e py")\n',
                {_BETA_BINARY},
                id="os_system_shell_string",
            ),
        ],
    )
    def test_the_POSITIVE_CONTROL_the_seam_really_does_resolve(
        self, tmp_path: Path, what: str, body: str, expected: set[str]
    ) -> None:
        """Every pin in §C is satisfied by a resolver that refuses everything — and a seam
        that resolves nothing derives an EMPTY set, over which layer 2 passes vacuously.
        That is the git-less image sailing through exactly as it did before this instrument
        existed. These five must resolve, silently and correctly.
        """
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="seam.py", body=body)

        derived, message = _derive(tmp_path, sanctioned=_SEAM_ONLY)

        assert derived == frozenset(expected), (
            f"the seam must resolve {what}: expected {sorted(expected)!r}, got "
            f"{sorted(derived or [])!r} (message: {message!r}). A resolver that refuses "
            f"everything gates NOTHING while looking strict — the derived set goes empty and "
            f"layer 2 passes over a container with nothing in it"
        )


# =========================================================================== #
# §D — WHAT THE OLD WORLD GOT RIGHT (the removed-behaviour inventory).
# =========================================================================== #
# The dual of the rename law (odoo-custom-v15 PR93): tests written for a NEW design certify
# only the new world, and nothing checks that the OLD world's virtues survived the rewrite.
# Every behaviour v2's contract pinned that is still CORRECT is re-pinned here, adjudicated:
#
#   preserved | the members come from the workspace, not a hardcoded list      → below
#   preserved | a new member grows the required set by itself                  → below
#   preserved | code that does not SHIP is not required of the image           → below
#   preserved | a scan over NO MODULES fails loud (the vacuous-gate pin)       → below
#   preserved | packages that exec nothing are a LEGITIMATE empty answer       → below
#   preserved | the three causes of an empty set have three distinct fates     → below
#   preserved | every Containerfile pin (unchanged, verbatim)                  → §E
#   DROPPED   | TestEverySpawnFormIsSeen — asserted a NON-sanctioned module's
#               subprocess.run/Popen/os.execvp/... RESOLVE to {"rg"}. Under the
#               sanctioned-seam architecture every one of those is now a LOUD
#               REFUSAL. The class certified the OLD world and is deliberately gone;
#               its successor is TestInsideTheSeamTheFormIsCanonical (which pins the
#               same spawn forms INSIDE the seam) plus §A (which pins the refusal
#               outside it). Nothing is un-pinned by the deletion.
#   DROPPED   | TestEveryExecSiteIsResolvedOrLoud + its _EXEC_SHAPES corpus — the
#               ∀-pin over a hand-listed nine-shape corpus. It is the defect, not a
#               casualty of it (see this file's header). Superseded by §A.
# =========================================================================== #
class TestTheDerivedSetForThisRepo:
    """The golden read — and why a RED here is a feature, not a chore."""

    def test_the_derived_set_is_exactly_the_binaries_the_image_must_carry(self) -> None:
        derived = required_binaries(_REPO_ROOT)

        assert derived == _TODAYS_DERIVED_SET, (
            f"the SHIPPED code's external-binary set changed: {sorted(derived)!r}. This set "
            f"is what the deploy demands of the image (layers 2/3). If a new binary appeared, "
            f"it must be INSTALLED IN THE IMAGE (Containerfile) before this pin is updated — "
            f"the whole point of deriving it is that nobody has to remember, and this RED is "
            f"the reminder (findings #125/#131: the image had no git, so the honesty line and "
            f"every snapshot's git_ref were silently null for three months)"
        )

    def test_the_scan_vouches_for_every_shipped_module_in_this_repo(self) -> None:
        # If this raises, some shipped module reached a process spawner outside the sanctioned
        # seam (or the seam's own argv[0] stopped being readable) — a HUMAN VERDICT is owed,
        # and the deploy must not proceed on a required set it cannot trust.
        required_binaries(_REPO_ROOT)


class TestTheDerivationIsReal:
    """Kills the build that hardcodes the answer or the member list."""

    def test_the_members_come_from_the_workspace_not_a_hardcoded_list(
        self, tmp_path: Path
    ) -> None:
        # THREE members, THREE seams, THREE different binaries, none of them this repo's. A
        # scan that walks a hardcoded ["lorescribe", "loresigil", "loremaster"], or only ONE
        # package, or that returns a hardcoded {"git"}, cannot pass this.
        _write_workspace(tmp_path, ["alpha", "beta", "gamma"])
        _write_member(tmp_path, "alpha", module="seam.py", body=_shellout(_ALPHA_BINARY))
        _write_member(tmp_path, "beta", module="seam.py", body=_shellout(_BETA_BINARY))
        _write_member(tmp_path, "gamma", module="seam.py", body=_shellout(_GAMMA_BINARY))
        seams = frozenset(
            {"alpha/alpha/seam.py", "beta/beta/seam.py", "gamma/gamma/seam.py"}
        )

        derived, message = _derive(tmp_path, sanctioned=seams)

        assert derived == frozenset({_ALPHA_BINARY, _BETA_BINARY, _GAMMA_BINARY}), (
            f"every SHIPPED workspace member must be scanned, and the binary set DERIVED from "
            f"their source — not hardcoded. Got {derived!r} / {message!r}"
        )
        assert "git" not in (derived or frozenset())

    def test_a_new_workspace_member_grows_the_required_set_by_itself(
        self, tmp_path: Path
    ) -> None:
        # A member added to the image (the workspace) must extend the required-binary set with
        # NO edit to the deploy or the probe. If someone has to remember, this repo's history
        # says they will not.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="seam.py", body=_shellout(_ALPHA_BINARY))
        assert required_binaries(tmp_path, sanctioned=_SEAM_ONLY) == frozenset({_ALPHA_BINARY})

        _write_workspace(tmp_path, ["alpha", "delta"])
        _write_member(tmp_path, "delta", module="seam.py", body=_shellout(_BETA_BINARY))
        both = _SEAM_ONLY | {"delta/delta/seam.py"}

        assert required_binaries(tmp_path, sanctioned=both) == frozenset(
            {_ALPHA_BINARY, _BETA_BINARY}
        )

    def test_code_that_does_not_SHIP_is_not_required_of_the_image(self, tmp_path: Path) -> None:
        # The other direction — an OVER-broad set is its own failure: it would make the deploy
        # demand binaries the image has no reason to carry (this repo's test trees and skill
        # scripts shell out to plenty). Only the INSTALLED package of each workspace member
        # runs in the image — so a test tree may exec freely, and the deny side must not even
        # LOOK at it.
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="seam.py", body=_shellout(_ALPHA_BINARY))
        tests = tmp_path / "alpha" / "tests"
        tests.mkdir(parents=True)
        (tests / "test_thing.py").write_text(_shellout(_UNSHIPPED_BINARY), encoding="utf-8")
        _write_member(tmp_path, "toolbox", module="seam.py", body=_shellout(_UNSHIPPED_BINARY))

        derived, message = _derive(tmp_path, sanctioned=_SEAM_ONLY)

        assert derived == frozenset({_ALPHA_BINARY}), (
            f"only the SHIPPED package of each workspace member may contribute to the required "
            f"set, and only it may be DENIED a spawner — {_UNSHIPPED_BINARY!r} came from a test "
            f"tree or a non-member directory, neither of which runs in the image. (If this "
            f"refused instead, the deny side is scanning test trees: every test file that "
            f"shells out would then have to be sanctioned, and the instrument dies of noise.) "
            f"Got {derived!r} / {message!r}"
        )


class TestTheEmptySetHasDistinctCauses:
    """**The OUTCOME is not the danger; the CAUSE is.** An empty set has four causes now, and
    they must not share a fate:

    * the scan found NO MODULES → dangerous → ``ShelloutScanError`` (a gate over nothing
      passes over everything);
    * a non-sanctioned module reaches a spawner → dangerous → ``UnresolvedExecSiteError``;
    * a sanctioned module's argv is unreadable, or it execs nothing → dangerous → raise;
    * the shipped packages genuinely exec nothing → **LEGITIMATE** ``frozenset()``, and the
      deploy says so in words.
    """

    def test_no_modules_is_dangerous_and_raises(self, tmp_path: Path) -> None:
        _write_workspace(tmp_path, [])
        with pytest.raises(ShelloutScanError):
            required_binaries(tmp_path, sanctioned=_NO_SEAM)

        # A root that is not a workspace at all (no pyproject) — same verdict.
        with pytest.raises(ShelloutScanError):
            required_binaries(tmp_path / "not-a-workspace", sanctioned=_NO_SEAM)

    def test_packages_that_exec_nothing_are_a_LEGITIMATE_empty_answer(
        self, tmp_path: Path
    ) -> None:
        # The discrimination that makes every "raise" pin above mean something: the scan must
        # not simply refuse every empty result. "Raise when empty" is satisfiable by a scan
        # that always raises — and that is not a derivation, it is a wall.
        _one_member(tmp_path, "def go() -> int:\n    return 1\n")

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived == frozenset(), (
            f"a shipped package that execs nothing requires no binary — an empty set here is "
            f"the CORRECT answer, and the scan refused it ({message!r})"
        )

    def test_an_unresolvable_argv0_names_the_LINE_not_just_the_file(
        self, tmp_path: Path
    ) -> None:
        _write_workspace(tmp_path, ["alpha"])
        _write_member(
            tmp_path,
            "alpha",
            module="seam.py",
            body=(
                "import subprocess\n"
                "\n"
                "\n"
                "def go(cmd: list[str]) -> None:\n"
                "    subprocess.run(cmd, check=False)\n"
            ),
        )

        with pytest.raises(UnresolvedExecSiteError) as raised:
            required_binaries(tmp_path, sanctioned=_SEAM_ONLY)

        message = str(raised.value)
        assert "seam.py" in message
        assert ":5" in message or "line 5" in message, (
            f"the raise must name the LINE of the unresolvable site, not just the file — "
            f"'somewhere in this module' is not a verdict a human can act on. Got: {message!r}"
        )


class TestTheProseMatchesTheMachine:
    """Served English that promises a mechanism which does not run is this repo's most
    expensive defect class (PKT-28 C1: ten instances in one phase). ``shellout.py``'s
    docstring is the prose a future author reads BEFORE writing the next shell-out — if it
    still describes v2's binding-following resolver, it teaches them to write code this scan
    will refuse, and to distrust the refusal when it comes.

    The second pin is the good kind: **DERIVED from the behaviour, not restated beside it.**
    The docstring must name every path in ``SANCTIONED_EXEC_MODULES`` — so the day the
    allowlist grows, the prose that describes it goes RED unless it grew too.
    """

    def test_the_docstring_does_not_promise_the_RETIRED_resolver(self) -> None:
        prose = " ".join(
            (shellout_module.__doc__ or "").split()
            + (ShelloutScanError.__doc__ or "").split()
        ).lower()

        for retired in ("through the module's own bindings", "empty answer is the dangerous one"):
            assert retired not in prose, (
                f"the docstring still promises the RETIRED design ({retired!r}). v2 followed "
                f"each module's BINDINGS to find its spawners; that is exactly the design "
                f"that lost, and the prose beside the code must not teach it to the next "
                f"author. Describe what the code now does: deny-by-default outside one "
                f"sanctioned seam, resolve precisely inside it"
            )
        assert "legitimate" in prose or "legal" in prose, (
            "the docstring must still say plainly that an empty set from packages which exec "
            "nothing is a LEGITIMATE answer — TestTheEmptySetHasDistinctCauses pins it, and "
            "the prose must not contradict the pins"
        )

    def test_the_docstring_NAMES_every_sanctioned_module(self) -> None:
        prose = shellout_module.__doc__ or ""

        for path in SANCTIONED_EXEC_MODULES:
            assert path in prose, (
                f"{path!r} is SANCTIONED to spawn processes and the module docstring does not "
                f"name it. The allowlist is the entire safe set; a reader must be able to see "
                f"what is in it without grepping for a constant. (This pin is DERIVED from "
                f"SANCTIONED_EXEC_MODULES, so it grows with the allowlist by itself — prose "
                f"that describes behaviour must be derived from the behaviour, not restated "
                f"beside it)"
            )


# =========================================================================== #
# §E — the image installs exactly what the scan gates (DEFECT-4, unchanged).
# =========================================================================== #
def _containerfile_text() -> str:
    return _CONTAINERFILE.read_text(encoding="utf-8")


def _apt_installed_binaries(text: str) -> set[str]:
    """The binaries the image apt-installs — parsed from the REAL Containerfile."""
    assert "apt-get install" in text, "the Containerfile no longer has an apt-get install line"
    tail = text.split("apt-get install", 1)[1]
    tail = tail.replace("\\\n", " ")
    tail = tail.split("&&")[0]
    tail = tail.split("\n")[0]
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


class TestTheImageInstallsExactlyWhatTheScanGates:
    """The image's binary set is a CHECKED variable, not a comment.

    * every binary the shipped code execs must be INSTALLED (the gate that catches #131 in
      the repo suite, before any container exists);
    * every binary the image installs must be GATED — or explicitly DECLARED ungated, with a
      reason, in the Containerfile itself;
    * the comment block that CITES the gate may name only binaries the gate actually covers.
    """

    def test_every_binary_the_shipped_code_execs_is_installed_by_the_image(self) -> None:
        derived = required_binaries(_REPO_ROOT)
        installed = _apt_installed_binaries(_containerfile_text())

        assert derived <= installed, (
            f"the shipped code execs {sorted(derived - installed)!r}, which the image does NOT "
            f"install. That is finding #131 exactly: the seam shells out, the binary is absent, "
            f"the helper swallows the OSError, and the field is a silent null in production "
            f"while every test on a git-having host stays green. Add it to the Containerfile's "
            f"apt line"
        )

    def test_the_image_installs_no_binary_that_no_gate_protects(self) -> None:
        derived = required_binaries(_REPO_ROOT)
        text = _containerfile_text()
        installed = _apt_installed_binaries(text)
        declared = _declared_ungated(text)

        undeclared = installed - derived - set(declared)

        assert not undeclared, (
            f"the image installs {sorted(undeclared)!r}, which the derived set does not contain "
            f"— so NO gate protects them, and nothing in the tree says so.\n"
            f"Two honest fixes, either is fine:\n"
            f"  (a) drop them from the apt line, or\n"
            f"  (b) DECLARE them, with a reason, in the Containerfile:\n"
            f"      # lore-ungated-binary: curl — reserved for a container healthcheck; no "
            f"shipped code execs it\n"
            f"An ungated binary is allowed. An ungated binary that the file CLAIMS is gated is "
            f"a false gate (DEFECT-4)"
        )

    def test_a_declared_ungated_binary_is_really_ungated_and_carries_a_reason(self) -> None:
        derived = required_binaries(_REPO_ROOT)
        declared = _declared_ungated(_containerfile_text())

        for binary, reason in declared.items():
            assert binary not in derived, (
                f"{binary!r} is declared UNGATED but the shipped code execs it — it IS gated "
                f"(layer 2 requires it). Delete the declaration"
            )
            assert len(reason) >= _MIN_REASON_CHARS, (
                f"the ungated declaration for {binary!r} carries no real reason ({reason!r}). An "
                f"exemption without evidence is the thing that blessed the bootstrap DDL right "
                f"before it lost 6-34% of concurrent first-connects"
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
                binary for binary in ungated if re.search(rf"\b{re.escape(binary)}\b", lowered)
            }
            assert not named, (
                f"this comment block cites the layer-2 gate ({_GATE_CITATIONS}) and names "
                f"{sorted(named)!r} — binaries the gate CANNOT cover, because the derived set "
                f"only ever contains what the shipped PYTHON execs. A reader is being told a "
                f"check exists that does not.\nBlock:\n{block}"
            )
