"""Contract for ``scripts/mutation_proof.py`` (finding #196).

**THE FINDING THIS EXISTS TO INSTRUMENT.** A mutation proof is the only evidence
that a pin can actually fail. Twice in one session it produced a green-looking
receipt while proving nothing, and the two failures are DIFFERENT:

1. **The mutation never landed** (#194). A guessed anchor matched nothing, the
   helper printed an error, and the shell block ran the test anyway — against an
   UNMUTATED tree. ``1 passed`` read as a proof. Guarded by: exactly-once anchor
   matching, and an exit code the caller cannot ignore.
2. **The mutation landed and reddened the WRONG TESTS.** This is the one that
   matters, and ``set -e`` does nothing about it: setup succeeded, a test went
   red, and the tail says ``1 failed`` — *identical to success*. The only thing
   that ever caught it was a human knowing which test SHOULD redden and noticing
   the count did not match. That is what gets mechanised here.

So the load-bearing property is the **two-way diff** against a set declared
BEFORE the run: unexpected reds, and — the direction people forget —
**declared reds that stayed GREEN**. The second catches a mutation that applies
cleanly into code no test exercises: it lands, it is real, and every pin passes.
A one-directional check calls that a pass.

⚠ **A DECLARED SET READ OFF THE OUTPUT IS THE TAUTOLOGY IN A NEW COSTUME.** The
helper cannot enforce that (nothing can distinguish a set typed from knowledge
from one transcribed after a peek), so it is stated in ``--help`` and lives with
the caller. This is a documented BOUND, not a closed hole.

⚠ **EVERY TEST HERE MUTATES A THROWAWAY SANDBOX UNDER ``tmp_path``, NEVER THIS
CHECKOUT** — the same trap ``test_tree_fingerprint.py`` documents, and worse: a
mutation harness proving itself against the live tree would corrupt concurrent
agents' gate receipts AND its own, intermittently and only under concurrency.

DEVIATION, disclosed: the sandbox is a plain directory, **not a ``git init``
repo**. The helper never consults git — it backs up and restores by CONTENT,
which is strictly stronger than any git check and works on an uncommitted tree.
A git repo in these fixtures would be SCENERY, and scenery in a fixture is how a
reader concludes a check exists that does not.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

_HELPER = Path(__file__).resolve().parent / "mutation_proof.py"

_TARGET = '''\
VALUE = "alpha"
UNREACHED = "no test in this sandbox reads this line"


def value() -> str:
    return VALUE
'''

_TESTS = '''\
from target import value


def test_alpha():
    assert value() == "alpha"


def test_beta():
    assert 1 + 1 == 2
'''


@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    """A throwaway package with one test that depends on the mutable line and one
    that does not — so "reddened the wrong test" is expressible, not hypothetical."""
    (tmp_path / "target.py").write_text(_TARGET)
    (tmp_path / "test_target.py").write_text(_TESTS)
    return tmp_path


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _prove(
    sandbox: Path,
    *,
    anchor: str,
    replacement: str = "",
    expect_red: tuple[str, ...] = ("test_target.py::test_alpha",),
    target: str = "target.py",
) -> subprocess.CompletedProcess[str]:
    """Run the helper against the sandbox and return the completed process."""
    args = [sys.executable, str(_HELPER), "--file", target, "--anchor", anchor]
    if replacement:
        args += ["--replacement", replacement]
    for node in expect_red:
        args += ["--expect-red", node]
    args += ["--", sys.executable, "-m", "pytest", "-q", "test_target.py"]
    return subprocess.run(args, cwd=sandbox, capture_output=True, text=True, check=False)


class TestTheTwoWayDiffIsTheWholePoint:
    """Three legs, and NONE of them is optional — each is a wrong proof that the
    others wave through."""

    def test_a_mutation_reddening_EXACTLY_the_declared_set_PASSES(self, sandbox: Path) -> None:
        """The positive control. Without it the two failing legs below prove only
        that the helper rejects things, which a ``sys.exit(1)`` also does."""
        result = _prove(sandbox, anchor='"alpha"', replacement='"mutated"')
        assert result.returncode == 0, (
            f"a mutation that landed and reddened exactly the declared test was REJECTED.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "mutation LANDED" in result.stdout, (
            "no 'mutation LANDED' receipt — the caller cannot tell setup from a no-op"
        )

    def test_an_UNEXPECTED_red_FAILS_even_though_something_DID_go_red(self, sandbox: Path) -> None:
        """⚠ THE CASE ``set -e`` CANNOT SEE. The mutation lands, a test goes red,
        and the tail reads ``1 failed`` — byte-identical to a successful proof.
        Only the declared set distinguishes them."""
        result = _prove(
            sandbox,
            anchor='"alpha"',
            replacement='"mutated"',
            expect_red=("test_target.py::test_beta",),
        )
        assert result.returncode != 0, (
            "a mutation that reddened test_alpha while test_beta was DECLARED passed the proof — "
            "the helper is counting failures instead of identifying them, which is exactly the "
            "'1 failed' tail that fooled two runs"
        )
        combined = result.stdout + result.stderr
        assert "test_target.py::test_alpha" in combined and "test_target.py::test_beta" in combined, (
            f"the mismatch report names neither side, so it cannot be diagnosed:\n{combined}"
        )

    def test_a_mutation_landing_in_UNREACHED_code_FAILS(self, sandbox: Path) -> None:
        """The direction people forget. The anchor matches, the edit is real, and
        NOTHING goes red — because no test reaches the line. A one-directional
        check (only 'were there unexpected reds?') calls this a pass, and the pin
        it was 'proving' has never been demonstrated to fail at all."""
        result = _prove(
            sandbox,
            anchor="no test in this sandbox reads this line",
            replacement="mutated",
        )
        assert result.returncode != 0, (
            "a mutation that reddened NOTHING passed the proof — the declared pin was never "
            "shown to fail, which is the entire claim a mutation proof makes"
        )
        combined = result.stdout + result.stderr
        assert "test_target.py::test_alpha" in combined, (
            f"the declared-but-green test is not named, so nobody can tell what did not fire:\n{combined}"
        )


class TestAMutationThatDoesNotLandIsLOUDAndLeavesNoTrace:
    """#194 verbatim: the anchor missed and the run continued."""

    @pytest.mark.parametrize(
        ("anchor", "why"),
        [
            # ⚠ EXPLICIT ASCII IDS, and not for tidiness. pytest ASCII-ESCAPES
            # non-ASCII in a parametrised node id (an em-dash becomes a literal
            # ``—``), so an id derived from these strings does not match what
            # a caller would write down. Caught by dogfooding this very helper
            # against its own suite: the declared node id could never match the
            # emitted one, and the proof reported a two-way mismatch on a
            # perfectly good mutation. Named ids keep the vocabulary the same in
            # the source and on the wire.
            pytest.param(
                "this string is nowhere in the file",
                "zero matches - the #194 shape",
                id="zero-matches",
            ),
            pytest.param(
                "VALUE",
                "two matches - ambiguous, so which site was proven is unknowable",
                id="two-matches",
            ),
        ],
    )
    def test_a_non_unity_anchor_FAILS_and_leaves_the_file_BYTE_EXACT(
        self, sandbox: Path, anchor: str, why: str
    ) -> None:
        before = _md5(sandbox / "target.py")
        result = _prove(sandbox, anchor=anchor, replacement="x")
        assert result.returncode != 0, f"anchor accepted ({why})"
        assert _md5(sandbox / "target.py") == before, "the file was modified despite a rejected anchor"
        assert "mutation LANDED" not in result.stdout, (
            "the helper claimed a landed mutation for an anchor it rejected — the receipt lies"
        )

    def test_the_expected_red_set_is_REQUIRED(self, sandbox: Path) -> None:
        """A proof with no declared set is the old world with extra steps."""
        result = subprocess.run(
            [
                sys.executable, str(_HELPER),
                "--file", "target.py",
                "--anchor", '"alpha"',
                "--", sys.executable, "-m", "pytest", "-q", "test_target.py",
            ],
            cwd=sandbox, capture_output=True, text=True, check=False,
        )
        assert result.returncode != 0, "the helper ran a proof with no expected-RED set declared"


class TestTheTreeIsAlwaysRestored:
    """The mutation is transient BY CONSTRUCTION. An agent that mutates a shared
    checkout and dies mid-run must not leave the mutation behind — a sibling's
    gate run would inherit it and nothing would say so."""

    @pytest.mark.parametrize(
        ("expect_red", "label"),
        [
            (("test_target.py::test_alpha",), "a PASSING proof"),
            (("test_target.py::test_beta",), "a FAILING proof"),
        ],
    )
    def test_the_file_is_restored_byte_exact(
        self, sandbox: Path, expect_red: tuple[str, ...], label: str
    ) -> None:
        before = _md5(sandbox / "target.py")
        _prove(sandbox, anchor='"alpha"', replacement='"mutated"', expect_red=expect_red)
        assert _md5(sandbox / "target.py") == before, f"the file was left mutated after {label}"

    def test_the_file_is_restored_when_the_COMMAND_ITSELF_dies(self, sandbox: Path) -> None:
        """The command is not pytest at all. Restoration must not depend on the
        run having produced parseable output — that is when it matters most."""
        before = _md5(sandbox / "target.py")
        result = subprocess.run(
            [
                sys.executable, str(_HELPER),
                "--file", "target.py",
                "--anchor", '"alpha"',
                "--replacement", '"mutated"',
                "--expect-red", "test_target.py::test_alpha",
                "--", sys.executable, "-c", "raise SystemExit(3)",
            ],
            cwd=sandbox, capture_output=True, text=True, check=False,
        )
        assert _md5(sandbox / "target.py") == before, "a crashed command left the mutation in the tree"
        assert result.returncode != 0, "a command that died without reporting was treated as a proof"


class TestTheNodeIdParserDoesNotMangleRealOutput:
    def test_a_failure_MESSAGE_containing_a_dash_separator_does_not_truncate_the_nodeid(
        self, sandbox: Path
    ) -> None:
        """pytest emits ``FAILED <nodeid> - <message>``, and the message routinely
        contains ' - ' too. Splitting on the LAST separator (or on whitespace)
        yields a node id that matches nothing, so every proof reports a spurious
        two-way mismatch and the helper becomes noise nobody trusts."""
        (sandbox / "test_target.py").write_text(
            "from target import value\n\n\n"
            "def test_alpha():\n"
            '    assert value() == "alpha", "left - right - middle"\n'
        )
        result = _prove(sandbox, anchor='"alpha"', replacement='"mutated"')
        assert result.returncode == 0, (
            f"a failure message containing ' - ' broke node-id parsing.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


class TestTheHelperStatesItsBounds:
    def test_help_states_the_BOUNDS(self) -> None:
        """The bounds are load-bearing and must be readable FROM THE TOOL. The
        declared-set-read-off-the-output hole in particular cannot be closed
        mechanically, so a caller who never learns of it will walk into it."""
        result = subprocess.run(
            [sys.executable, str(_HELPER), "--help"], capture_output=True, text=True, check=True
        )
        for expected in ("BEFORE", "both ways", "restore", "BOUND"):
            assert expected in result.stdout, (
                f"--help does not state the bound {expected!r}:\n{result.stdout}"
            )
