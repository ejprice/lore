"""Contract — finding #138: the sanctioned-exec seam's dynamic-reach PERIMETER.

``loremaster.shellout`` gates every shell-out the shipped image can make (findings
#125/#131). Its CORE — import denial plus the receiver-blind os/asyncio spawn-API deny —
is the part a cold audit could not break. Its dynamic-reach PERIMETER is a different story:
the cold re-audit (``REPORT-pkt01-audit-1.md``, ``# FINAL RE-AUDIT (exec seam)`` §2) found
**five evasion doors**, and the module's own prose claims there are none.

THE THREAT MODEL — the load-bearing thing that was never written down
--------------------------------------------------------------------
This gate exists to catch an **HONEST DEVELOPER** who adds a shell-out while the image
silently lacks the binary. That is finding **#131** verbatim: the seam shelled out to a
``git`` that was not in the image, the ``OSError`` was swallowed into a silent
``(None, None)``, and no test could see it because tests run on a dev host that HAS git —
three months of empty snapshot provenance, green on every gate.

It is **NOT** a security boundary against a hostile author. Anyone who can commit to this
repo can already ship anything. *"A clever attacker gets through"* is therefore **not a
defect for this gate**; *"an honest engineer's shell-out goes unnoticed"* **is**. Every pin
below is graded against that model, and it is why doors 09-12 are pinned as a KNOWN BOUND
rather than closed: closing them receiver-blindly would refuse four shipped modules that use
``getattr``/``vars``/``globals``/``sys.modules`` legitimately, buying nothing against the
only adversary this gate has — an honest one who made a mistake.

THE OPERATOR RULING (finding #138)
----------------------------------
Close ONE door, fix the PROSE, ledger the rest.

* **Door 13 — the only door an HONEST author could actually hit — is CLOSED.**
  ``from loremaster.index import snapshots; snapshots.subprocess.run([...])`` reaches a
  spawner *through the sanctioned seam's own namespace*: the seam imports ``subprocess``, so
  it implicitly re-exports it, and ``subprocess`` is not a spawn PRIMITIVE (only the
  os/asyncio API is), so ``snapshots.subprocess.run`` walked straight through. This is not
  obfuscation — it is a plausible mistake, and it is the only one of the five that is. The
  fix denies the spawn-capable module NAMES as identifiers, at **zero false-positive cost**
  (re-derived below and in ``REPORT-pkt01-contract-5.md``: across all 78 shipped modules,
  the only Name/Attribute nodes matching a spawn-capable module name are the seam's own two
  ``subprocess`` references, which the deny side never inspects).

* **The PROSE stops overclaiming.** ``shellout.py`` claimed *"there is nothing here for a
  clever shape to evade"* and *"Any doubt is a refusal"* — both FALSE (four doors survive by
  design). Those sentences are what a future author trusts when they decide not to re-check
  the perimeter, and served English that promises a mechanism it does not run is this repo's
  most expensive defect class (PKT-28 C1: ten instances in one phase). The prose must make
  no absolute claim it cannot keep, and must carry the threat model above.

* **Doors 09-12 are a KNOWN BOUND (#138), pinned — not closed.** Same instrument as finding
  #137's third-party bound: pins that ASSERT THE MISS and go RED the day a future build ever
  closes them, so the bound is met deliberately instead of rediscovered and re-opened as a
  settled trade.

How to run:
    uv run pytest loremaster/tests/test_shellout_seam_perimeter.py -n auto -q
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
from loremaster.shellout import (
    _SPAWN_CAPABLE_MODULES,
    ShelloutScanError,
    _shipped_modules,
    required_binaries,
)

# The REAL repo root, resolved from THIS FILE (the test tree always lives in the real
# checkout, even when the package under test is PYTHONPATH-shadowed by a scratch build).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SHELLOUT_SOURCE = _REPO_ROOT / "loremaster" / "loremaster" / "shellout.py"

# The synthetic SEAM — foreign member, foreign module name, foreign path, foreign binary
# (this repo's #1 defect class is a fixture whose value the code can special-case; a build
# that hardcodes ``loremaster``/``snapshots.py``/``git`` fails every fixture below).
_SEAM = "alpha/alpha/seam.py"
_SEAM_ONLY = frozenset({_SEAM})
_NO_SEAM: frozenset[str] = frozenset()
_SEAM_BINARY = "rg"


# --------------------------------------------------------------------------- #
# Fixture plumbing (self-contained; mirrors test_shellout_allowlist.py's idiom)
# --------------------------------------------------------------------------- #
def _write_workspace(root: Path, members: list[str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "synthetic"\nversion = "0.0.0"\n\n'
        "[tool.uv.workspace]\n"
        f"members = {json.dumps(members)}\n",
        encoding="utf-8",
    )


def _write_member(root: Path, member: str, *, module: str, body: str) -> None:
    package = root / member / member
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / module).write_text(body, encoding="utf-8")


def _seam_body() -> str:
    """The sanctioned seam: imports ``subprocess`` plainly and execs the foreign binary.

    Because it ``import subprocess``, it implicitly RE-EXPORTS it as ``seam.subprocess`` —
    which is the entire mechanism of door 13.
    """
    return (
        "import subprocess\n"
        "\n"
        "\n"
        "def go() -> None:\n"
        f'    subprocess.run(["{_SEAM_BINARY}", "--version"], check=False)\n'
        "\n"
        "\n"
        "def status() -> str:\n"
        '    return "ok"\n'
    )


def _derive(
    root: Path, *, sanctioned: frozenset[str] = _NO_SEAM
) -> tuple[frozenset[str] | None, str]:
    """``(derived_set, "")`` when the scan VOUCHED, or ``(None, message)`` when it refused."""
    try:
        return required_binaries(root, sanctioned=sanctioned), ""
    except ShelloutScanError as raised:
        return None, str(raised)


def _workspace_with_seam(root: Path, consumer_body: str) -> None:
    """A workspace with the sanctioned seam AND a second module that tries to reach it."""
    _write_workspace(root, ["alpha"])
    _write_member(root, "alpha", module="seam.py", body=_seam_body())
    _write_member(root, "alpha", module="consumer.py", body=consumer_body)


# =========================================================================== #
# §1 — DOOR 13 IS CLOSED: reaching a spawner through the seam's own namespace.
# =========================================================================== #
class TestDoor13ClosedThroughTheSeamNamespace:
    """The one door an HONEST author could hit — the seam re-exports ``subprocess``.

    The fix denies the spawn-capable module NAMES (``subprocess``/``pty``/``ctypes``/…) as
    identifiers in a non-sanctioned module. That closes EVERY route that names such a module
    without importing it — the seam-namespace reach being the plausible one — and it is the
    receiver-blind, allowlist-the-safe posture the core already uses for the spawn API.
    """

    def test_positive_control_a_plain_import_is_already_refused(self, tmp_path: Path) -> None:
        """CONTROL. The seam-namespace reach must be judged against a door the scan ALREADY
        shuts, so a RED on the door-13 pins means 'this specific reach walks through', not
        'the whole gate is off'. A plain ``import subprocess`` in the consumer is refused on
        HEAD and on the fixed build alike.
        """
        _workspace_with_seam(tmp_path, 'import subprocess\n\nsubprocess.run(["fd"])\n')

        derived, message = _derive(tmp_path, sanctioned=_SEAM_ONLY)

        assert derived is None, (
            f"a plain `import subprocess` in a NON-sanctioned module resolved to "
            f"{sorted(derived or [])!r} instead of refusing — the base gate is not even "
            f"closed, so nothing downstream is meaningful"
        )
        assert "consumer.py" in message

    @pytest.mark.parametrize(
        ("shape", "consumer_body"),
        [
            pytest.param(
                "seam.subprocess.run — the audit's exact door 13",
                "from alpha import seam\n\n\n"
                "def go() -> None:\n"
                '    seam.subprocess.run(["fd", "-v"], check=False)\n',
                id="seam_subprocess_run",
            ),
            pytest.param(
                "the dotted form of the same reach",
                "import alpha.seam\n\n\n"
                "def go() -> None:\n"
                '    alpha.seam.subprocess.Popen(["fd"])\n',
                id="dotted_seam_subprocess_popen",
            ),
        ],
    )
    def test_reaching_a_spawner_through_the_seam_namespace_fails_loud(
        self, tmp_path: Path, shape: str, consumer_body: str
    ) -> None:
        """RED ON HEAD, GREEN ON THE FIX.

        ``snapshots.subprocess.run([...])`` is a plausible honest mistake: a developer wanting
        to shell out imports the one module that is allowed to, and reaches its re-exported
        ``subprocess``. On HEAD this VOUCHES (``subprocess`` is not a spawn primitive; ``run``
        is not either), so the shell-out ships with the deploy none the wiser — #131's shape,
        one import removed. Outside the seam, naming a spawn-capable module must be a refusal.
        """
        root = tmp_path / "ws"
        _workspace_with_seam(root, consumer_body)

        derived, message = _derive(root, sanctioned=_SEAM_ONLY)

        assert derived is None, (
            f"{shape}: a NON-sanctioned module reached a process spawner through the seam's "
            f"own namespace and the scan vouched for {sorted(derived or [])!r}. The seam "
            f"re-exports every spawn-capable module it imports; a module that NAMES one "
            f"(``subprocess``/``pty``/``ctypes``/…) as an identifier without importing it can "
            f"only have obtained it from another namespace, and the scan cannot follow that — "
            f"so it must refuse, naming file:line (finding #138)"
        )
        assert "consumer.py" in message and re.search(r":\d+|line \d+", message), (
            f"the refusal must name file:line so a human can rule on it. Got: {message!r}"
        )

    def test_NEGATIVE_CONTROL_ordinary_cross_module_attribute_stays_silent(
        self, tmp_path: Path
    ) -> None:
        """A PROBE NEEDS A CONTROL — and this one is load-bearing.

        The sanctioned seam is IMPORTED by real shipped code (the indexer imports
        ``snapshots``). The door-13 fix must refuse only ``seam.<spawn-capable-module>`` — NOT
        ordinary cross-module attribute access like ``seam.status()`` or ``seam.go()``. If it
        over-refuses here, every consumer of the seam becomes a false positive and the gate is
        deleted within the week. Re-derived over the real tree: zero shipped module outside
        the seam names any spawn-capable module as an identifier, so this control is exactly
        the shipped reality.
        """
        root = tmp_path / "ws"
        _workspace_with_seam(
            root,
            "from alpha import seam\n\n\n"
            "def use() -> str:\n"
            "    seam.go()\n"
            "    return seam.status()\n",
        )

        derived, message = _derive(root, sanctioned=_SEAM_ONLY)

        assert derived == frozenset({_SEAM_BINARY}), (
            f"reaching the seam for an ORDINARY attribute (``seam.go``/``seam.status``) was "
            f"refused ({message!r}). The fix denies only the spawn-capable MODULE names re-"
            f"exported by the seam — a gate that refuses honest consumers of the seam is a "
            f"gate that gets switched off. Expected the seam's own {{'rg'}}, unperturbed"
        )

    def test_the_fix_leaves_ordinary_spawn_free_modules_untouched(self, tmp_path: Path) -> None:
        """The negative control at repo scale: the derived set for THIS repo is unchanged.

        The whole point of the zero-FP re-derivation is that closing door 13 costs nothing.
        The shipped tree still derives exactly its one binary, with zero refusals — proven
        here against the real workspace so a build that closes the door by over-refusing
        (breaking the derivation) fails loudly.
        """
        # Not an isolated fixture — the real repo. On HEAD and on the fixed build this is
        # ``{'git'}``; a fix that introduces a false positive would RAISE instead.
        assert required_binaries(_REPO_ROOT) == frozenset({"git"}), (
            "the door-13 fix must not change the derived set for this repo: no shipped module "
            "outside the seam names a spawn-capable module as an identifier, so the only "
            "legal outcome is the unchanged {'git'}"
        )
        _ = tmp_path  # keep the signature uniform with the rest of the class


# =========================================================================== #
# §2 — DOORS 09-12 ARE A KNOWN BOUND (#138). Pinned, NOT closed.
# =========================================================================== #
class TestDoors09To12AreAKnownBound:
    """Same instrument as finding #137's third-party bound: ASSERT THE MISS.

    These four doors reach a spawner without ever naming one as an identifier — the primitive
    is a STRING KEY (``modules["subprocess"]``), or the reach is through a rebound builtin
    (``fetch = getattr``). Closing them receiver-blindly refuses four shipped modules that use
    those same doors legitimately, for no gain against an honest author — so the operator
    ruled them a KNOWN BOUND. Each pin below documents that the door walks through TODAY, and
    goes **RED the day a future build closes it**. A RED here is not a regression: it means a
    reviewer deliberately paid the false-positive cost, and should delete the pin and say so
    (finding #138) — a bound met on purpose, never rediscovered.
    """

    @pytest.mark.parametrize(
        ("door", "consumer_body"),
        [
            pytest.param(
                "door 09 — `from sys import modules` → modules['subprocess']",
                'from sys import modules\n\n\n'
                "def go() -> None:\n"
                '    modules["subprocess"].run(["fd"])\n',
                id="door09_from_sys_import_modules",
            ),
            pytest.param(
                "door 10 — `s = sys` → s.modules['subprocess']",
                "import sys\n\ns = sys\n\n\n"
                "def go() -> None:\n"
                '    s.modules["subprocess"].run(["fd"])\n',
                id="door10_sys_rebound",
            ),
            pytest.param(
                "door 11 — `fetch = getattr` → fetch(os, 'system')",
                'import os\n\nfetch = getattr\n\n\n'
                "def go() -> None:\n"
                '    fetch(os, "system")("fd -v")\n',
                id="door11_getattr_rebound",
            ),
            pytest.param(
                "door 12 — globals()['__builtins__']['__import__']('subprocess')",
                "def go() -> None:\n"
                '    globals()["__builtins__"]["__import__"]("subprocess").run(["fd"])\n',
                id="door12_globals_builtins",
            ),
        ],
    )
    def test_a_known_bound_door_still_walks_through(
        self, tmp_path: Path, door: str, consumer_body: str
    ) -> None:
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="consumer.py", body=consumer_body)

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived == frozenset(), (
            f"{door} is a KNOWN BOUND of the deny side (finding #138): it reaches a spawner "
            f"without naming one as an identifier, so the scan does not see it and vouches for "
            f"an EMPTY set. This pin asserts that miss ON PURPOSE. It just went a different "
            f"way — got {sorted(derived or [])!r} / {message!r}.\n"
            f"If you CLOSED this door deliberately (paying the false-positive cost of refusing "
            f"the shipped modules that use getattr/vars/globals/sys.modules legitimately), "
            f"that is a settled trade being re-opened — DELETE this pin and say so in your "
            f"report. If it changed by accident, you have narrowed the deny side without "
            f"meaning to"
        )


# =========================================================================== #
# §3 — THE PROSE. No absolute it cannot keep; it carries the threat model.
# =========================================================================== #
def _shellout_string_literals() -> list[str]:
    """Every string-literal constant in ``shellout.py`` — module + function docstrings,
    plain strings, and the literal segments of f-strings (an ``ast.walk`` visits the
    ``JoinedStr``'s ``Constant`` children with no special-casing). The text-hygiene idiom
    (``test_text_hygiene.py``), scoped to the one file finding #138 governs.
    """
    tree = ast.parse(_SHELLOUT_SOURCE.read_text(encoding="utf-8"), filename=str(_SHELLOUT_SOURCE))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _normalise(literals: list[str]) -> str:
    """Whitespace-collapsed, lower-cased join of every literal — reword-insensitive."""
    return " ".join(" ".join(literal.split()) for literal in literals).lower()


class TestTheProseDoesNotOverclaimThePerimeter:
    """Served English that promises a mechanism it does not run is this repo's costliest
    defect class. These pins are DELIBERATELY LOOSE: they forbid the specific absolute claims
    the audit proved false and require the threat-model substance the operator ruled — a
    truthful REWORD keeps passing; a re-introduced absolute, or a dropped threat model, goes
    RED.
    """

    @pytest.mark.parametrize(
        ("banned", "why"),
        [
            pytest.param(
                "nothing here for a clever shape to evade",
                "categorically false — the re-audit found five shapes that evade the deny "
                "side (doors 09-13), four of them KNOWN BOUNDS by design",
                id="nothing_to_evade",
            ),
            pytest.param(
                "any doubt is a refusal",
                "false — doors 09-12 are doubtful reaches (a spawner obtained through "
                "sys.modules / a rebound getattr) that are NOT refused; the scan never sees "
                "the doubt to act on it",
                id="any_doubt_is_a_refusal",
            ),
        ],
    )
    def test_the_prose_makes_no_absolute_claim_it_cannot_keep(
        self, banned: str, why: str
    ) -> None:
        """RED ON HEAD (both phrases present, at shellout.py:27/295/299), GREEN ON THE FIX.

        Loose polarity: only the two categorically-false absolutes are forbidden. The builder
        is free to describe the deny side's real posture ('a signal it cannot vouch for is a
        refusal', 'the shape game is unwinnable for an honest author') — those are TRUE and
        pass. What must not survive is a sentence a future author reads as 'the perimeter is
        complete, do not re-check it'.
        """
        prose = _normalise(_shellout_string_literals())

        assert banned not in prose, (
            f"shellout.py's prose still makes the absolute claim {banned!r}, which is {why}. "
            f"That sentence is what a future author trusts when they decide NOT to re-check "
            f"the perimeter — and served English that promises a mechanism the code does not "
            f"run is this repo's most expensive defect class (PKT-28 C1). Describe the real, "
            f"bounded posture instead (finding #138)"
        )

    def test_the_prose_carries_the_threat_model(self) -> None:
        """RED ON HEAD (none of the three substances present), GREEN ON THE FIX.

        The prose is the ONLY place the threat model can live — no gate encodes 'who this is
        for'. It must name (a) the actor it protects against (an honest developer's unnoticed
        shell-out), (b) the actor it does NOT (a hostile author, against whom it is not a
        security boundary), and (c) the ledgered dynamic-reach bound (#138) the surviving
        doors belong to. Each is checked as SUBSTANCE, not wording — any of several stems
        satisfies the hostile-actor clause, so the builder keeps full freedom of phrasing.
        """
        prose = _normalise(_shellout_string_literals())

        assert "honest" in prose, (
            "the prose must name the actor this gate is FOR — an honest developer whose "
            "shell-out goes unnoticed when the image lacks the binary (finding #131). Without "
            "it, the next author cannot tell a false positive (cheap: a human ruling) from a "
            "false negative (three months of null git_ref)"
        )
        assert any(stem in prose for stem in ("hostile", "attacker", "malicious", "adversar")), (
            "the prose must state that this is NOT a security boundary against a hostile "
            "author — anyone who can commit here can already ship anything, so 'a clever "
            "attacker gets through' is not a defect for this gate. Omitting this invites the "
            "next author to try to close doors 09-12 and pay the false-positive cost for "
            "nothing (finding #138)"
        )
        assert "#138" in prose, (
            "the surviving dynamic-reach doors (09-12) must be LEDGERED in the prose by their "
            "finding id (#138), exactly as the third-party-dependency bound is ledgered "
            "today. A bound named in the code is a bound the next engineer meets deliberately "
            "instead of rediscovering it in the next audit and re-opening a settled trade"
        )


class TestTheProseFixDoesNotRegressTheExistingProsePins:
    """The removed-behaviour inventory (PR93 dual): the prose rewrite must keep every virtue
    the EXISTING prose pins (test_shellout_allowlist.py::TestTheProseMatchesTheMachine)
    already guard. Re-pinned here so a #138 reword that drops one fails in THIS file too,
    next to the change that would cause it.
    """

    def test_the_empty_set_is_still_called_legitimate(self) -> None:
        prose = _normalise(_shellout_string_literals())
        assert "legitimate" in prose or "legal" in prose, (
            "the reword dropped the plain statement that an empty set from packages which exec "
            "nothing is a LEGITIMATE answer — TestTheEmptySetHasDistinctCauses pins that "
            "behaviour, and the prose must not contradict it"
        )

    def test_the_retired_v2_resolver_is_still_not_described(self) -> None:
        prose = _normalise(_shellout_string_literals())
        for retired in ("through the module's own bindings", "empty answer is the dangerous one"):
            assert retired not in prose, (
                f"the reword re-introduced the RETIRED v2 design ({retired!r}) — the "
                f"binding-following resolver that lost. The prose beside the code must not "
                f"teach the next author a design this scan refuses"
            )


# =========================================================================== #
# §4 — THE DENY SET MAY HOLD ONLY MODULES THAT EXIST (audit LAST-1).
#
# Door 13's fix denies the spawn-capable module NAMES as identifiers. That is right, and it
# must not be weakened. But the set it reads, ``_SPAWN_CAPABLE_MODULES``, carries three names
# that ARE NOT IMPORTABLE MODULES on Python 3.14: ``commands`` and ``popen2`` are Python-2
# relics, and ``imp`` was removed in 3.12. Denying them:
#
#   * buys NOTHING — no module can reach a spawner through a module that does not exist; and
#   * costs a live FALSE POSITIVE — ``commands`` is an ordinary English word. The derivation
#     runs inside the deploy's layer-2 gate, so ONE innocent ``self.commands`` in a shipped
#     module fails ``verb_start`` for EVERY project, telling its author their CLI attribute
#     "names a process-spawn module".
#
# That is the insult that gets an instrument switched off — and per this file's own threat
# model, a gate that refuses honest code is a gate that gets switched off, whereupon #131
# happens again with nothing watching at all. Cost TODAY is zero (no shipped module uses the
# words), which is exactly why it must be fixed now rather than discovered by the first author
# who writes one.
#
# THE BOUNDARY IS THE WHOLE POINT. ``posix`` is an ordinary-looking word too — and a REAL,
# importable module on 3.14. It stays denied. The property is not "sweep out the odd-looking
# names"; it is "the deny set holds exactly the modules that EXIST and can spawn".
# =========================================================================== #

# The three names that are NOT importable modules on the interpreter the image runs.
_DEAD_MODULE_NAMES = ("commands", "imp", "popen2")

# The spawn-capable modules that ARE importable — hand-written ON PURPOSE. Deriving this from
# ``_SPAWN_CAPABLE_MODULES`` would make the boundary pins tautological: a build that "fixed"
# the false positive by EMPTYING the deny set would sail through. This list is the answer to
# "what wrong build would this fixture still pass?".
_LIVE_SPAWN_MODULE_NAMES = (
    "subprocess",
    "pty",
    "multiprocessing",
    "posix",
    "_posixsubprocess",
    "ctypes",
    "webbrowser",
)


def _ordinary_use(name: str, shape: str) -> str:
    """A module body that uses ``name`` as an ORDINARY identifier — and execs nothing.

    Every shape here puts ``name`` in a ``Name`` or ``Attribute`` node, because those are the
    only nodes ``_deny_identifier`` is called on. A parameter that is never READ
    (``def run_all(commands: list[str]) -> None: ...``) is an ``ast.arg``, which the scan never
    visits — it passes on HEAD already, so it is not a fixture that can discriminate anything
    and it is deliberately not used here.
    """
    return {
        # The audit's second reproduction, verbatim.
        "attribute": (
            f"class Runner:\n    def __init__(self) -> None:\n        self.{name}: list[str] = []\n"
        ),
        # The audit's FIRST reproduction, honestly spelled: a parameter that is actually READ
        # (nobody declares a parameter they never use).
        "parameter": (
            f"def run_all({name}: list[str]) -> None:\n"
            f"    for item in {name}:\n        print(item)\n"
        ),
        "local_variable": f"def go() -> int:\n    {name} = [1, 2]\n    return len({name})\n",
        "loop_variable": (
            f"def go(items: list[int]) -> None:\n    for {name} in items:\n        print({name})\n"
        ),
        "class_attribute": f"class C:\n    {name} = 0\n\n\ndef go(c: C) -> int:\n    return c.{name}\n",
    }[shape]


class TestDeadModuleNamesAreNotDenied:
    """A name that is not a module cannot be a route to a spawner — so denying it is all cost.

    RED ON HEAD (the false positive fires TODAY), GREEN ON THE FIX.
    """

    def test_POSITIVE_CONTROL_the_same_shape_with_a_LIVE_module_name_IS_refused(
        self, tmp_path: Path
    ) -> None:
        """A PROBE NEEDS A CONTROL — this is the one that makes every PASS below mean something.

        The pins in this class assert that a body is NOT refused. A ``PASS`` is only evidence
        if the same fixture machinery can produce a ``REFUSE`` — otherwise a build that
        disabled the identifier rule entirely (or a fixture harness that silently scanned
        nothing) would look identical to the correct fix. So: the byte-for-byte same shape,
        with a LIVE module name in place of the dead one, must still fail loud.
        """
        _write_workspace(tmp_path, ["alpha"])
        _write_member(
            tmp_path, "alpha", module="consumer.py", body=_ordinary_use("subprocess", "attribute")
        )

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived is None, (
            f"``self.subprocess: list[str] = []`` was VOUCHED for ({sorted(derived or [])!r}). "
            f"``subprocess`` is a real, importable, spawn-capable module: naming it without "
            f"importing it means holding it through another namespace, and that is door 13. "
            f"If this passes, the identifier rule is off and every PASS in this class is "
            f"meaningless"
        )
        assert "subprocess" in message

    @pytest.mark.parametrize("dead_name", _DEAD_MODULE_NAMES)
    @pytest.mark.parametrize(
        "shape", ["attribute", "parameter", "local_variable", "loop_variable", "class_attribute"]
    )
    def test_an_ordinary_identifier_that_is_not_a_module_is_not_refused(
        self, tmp_path: Path, dead_name: str, shape: str
    ) -> None:
        """``self.commands`` / ``for imp in items`` — code that execs NOTHING — must scan clean.

        On HEAD every one of these is REFUSED, over a word that is not a module. The scan
        cannot be reached through ``commands``/``imp``/``popen2`` because there is nothing at
        the other end: ``import commands`` raises ``ModuleNotFoundError`` on the image's own
        interpreter (``python:3.14-slim``). The deny side is an over-approximation of REACHES
        TO A SPAWNER, not a reserved-word list.
        """
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module="consumer.py", body=_ordinary_use(dead_name, shape))

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived == frozenset(), (
            f"a shipped module using {dead_name!r} as an ordinary {shape} — it execs NOTHING — "
            f"was REFUSED: {message!r}.\n"
            f"{dead_name!r} is not an importable module on Python 3.14 (the image's own "
            f"interpreter), so no module can reach a process spawner through it and denying "
            f"the name buys NOTHING. What it costs is real: the derivation runs inside the "
            f"deploy's layer-2 gate, so one innocent ``self.commands`` fails ``verb_start`` for "
            f"EVERY project. A gate that refuses honest code is a gate that gets switched off, "
            f"and then #131 happens again with nothing watching at all (audit LAST-1)"
        )

    @pytest.mark.parametrize("dead_name", _DEAD_MODULE_NAMES)
    @pytest.mark.parametrize(
        ("shape", "consumer_body_template"),
        [
            pytest.param("import", "import alpha.{name}\n", id="import_dotted"),
            pytest.param("from-import", "from alpha import {name}\n", id="from_import"),
        ],
    )
    def test_a_shipped_SUBMODULE_named_like_a_dead_module_can_be_imported(
        self, tmp_path: Path, dead_name: str, shape: str, consumer_body_template: str
    ) -> None:
        """The shape the audit did NOT try — and the likeliest false positive of the lot.

        ``commands.py`` is one of the most ordinary module names in Python. On HEAD a shipped
        package cannot even contain one: ``_deny_import``/``_deny_import_from`` split the
        dotted path and intersect it with ``_SPAWN_CAPABLE_MODULES``, so ``import
        alpha.commands`` and ``from alpha import commands`` are both refused — over a
        first-party module of our own. This is the same defect as the identifier ban, one rule
        along, and the same one-line deletion fixes both (which is why the fix is DELETION from
        the set, not a special case inside one rule).
        """
        _write_workspace(tmp_path, ["alpha"])
        _write_member(tmp_path, "alpha", module=f"{dead_name}.py", body="VERBS = ['ship']\n")
        _write_member(
            tmp_path,
            "alpha",
            module="consumer.py",
            body=consumer_body_template.format(name=dead_name),
        )

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived == frozenset(), (
            f"a shipped package containing a FIRST-PARTY module named {dead_name}.py could not "
            f"be {shape}ed: {message!r}. The path is split and intersected with the "
            f"spawn-capable set, so our own module collides with a Python-2 relic that does not "
            f"exist. Nothing is reachable through it — it is OUR file"
        )


class TestLiveSpawnModuleNamesAreStillRefused:
    """THE BOUNDARY. Door 13's fix must survive the LAST-1 fix intact.

    Deleting the dead names must not become "delete the odd-looking names". ``posix`` looks
    every bit as archaic as ``popen2`` and is a REAL, importable, spawn-capable module on 3.14
    — it stays denied. These pins are the ones that go RED if a fix over-reaches.
    """

    @pytest.mark.parametrize("live_name", _LIVE_SPAWN_MODULE_NAMES)
    def test_naming_a_live_spawn_module_through_the_SEAM_namespace_is_refused(
        self, tmp_path: Path, live_name: str
    ) -> None:
        """Door 13, re-pinned per spawn-capable module: ``seam.<module>.run(...)``.

        For ``subprocess`` this is the audit's exact door-13 reproduction. The call is spelled
        ``.run(...)`` for every module on purpose: ``run`` is not a spawn PRIMITIVE, so the only
        thing that can refuse these bodies is the module-NAME rule — a refusal here therefore
        proves the rule fired for the RIGHT reason, not that some other check happened to trip.
        """
        root = tmp_path / "ws"
        _workspace_with_seam(
            root,
            "from alpha import seam\n\n\ndef go() -> None:\n"
            f'    seam.{live_name}.run(["fd", "-v"])\n',
        )

        derived, message = _derive(root, sanctioned=_SEAM_ONLY)

        assert derived is None, (
            f"a NON-sanctioned module reached {live_name!r} through the sanctioned seam's "
            f"re-exported namespace and the scan VOUCHED for {sorted(derived or [])!r}. "
            f"{live_name!r} IS an importable, spawn-capable module on Python 3.14 — this is "
            f"door 13, and closing it is what commit 0101f9b was for. Removing the DEAD names "
            f"({', '.join(_DEAD_MODULE_NAMES)}) from the deny set must not remove a LIVE one"
        )
        assert live_name in message, (
            f"the refusal must name the module a human has to rule on. Got: {message!r}"
        )

    @pytest.mark.parametrize("live_name", _LIVE_SPAWN_MODULE_NAMES)
    def test_naming_a_live_spawn_module_as_a_BARE_NAME_is_refused(
        self, tmp_path: Path, live_name: str
    ) -> None:
        """The receiver-blind half: a bare ``Name`` load, no seam and no import in sight.

        A module that names a spawn-capable module without importing it (an import would
        already have been refused) can only be holding it through some OTHER namespace, which
        the scan cannot follow. That is a refusal, whatever the shape.
        """
        _write_workspace(tmp_path, ["alpha"])
        _write_member(
            tmp_path, "alpha", module="consumer.py", body=f"def go() -> object:\n    return {live_name}\n"
        )

        derived, message = _derive(tmp_path, sanctioned=_NO_SEAM)

        assert derived is None, (
            f"a bare reference to the live spawn-capable module {live_name!r} was vouched for "
            f"({sorted(derived or [])!r}) — the identifier deny has been narrowed past the "
            f"three dead names it was meant to lose"
        )
        assert live_name in message


class TestTheDenySetHoldsOnlyModulesThatExist:
    """THE INSTRUMENT — so this defect CLASS cannot come back (a fix without an invariant is
    half a fix).

    The pins above are behavioural and would go red for THESE three names. This one states the
    PROPERTY they are instances of, derived from the interpreter rather than from a hand-list:
    *every name the scan denies as a spawn-capable module must actually BE one*. A future
    author who adds another relic — or a stdlib module that is removed in a later Python — goes
    RED here automatically, with no one having to remember this lesson.
    """

    def test_every_denied_spawn_module_is_importable_on_this_interpreter(self) -> None:
        """RED ON HEAD (``commands``, ``imp``, ``popen2``), GREEN ON THE FIX.

        Denying a name that resolves to no module is pure false-positive surface: it can refuse
        honest code and it can never prevent a spawn, because there is nothing at the other end
        of the name to spawn WITH.
        """
        dead = sorted(
            name
            for name in _SPAWN_CAPABLE_MODULES
            if importlib.util.find_spec(name) is None  # never raises: all names are top-level
        )

        assert dead == [], (
            f"_SPAWN_CAPABLE_MODULES denies {dead!r} — name(s) that do not resolve to an "
            f"importable module on Python {sys.version_info.major}.{sys.version_info.minor}, "
            f"the interpreter the image itself runs. A module cannot reach a process spawner "
            f"through a module that does not exist, so each of these is ALL COST (a live "
            f"false positive on an ordinary English word, failing ``verb_start`` for every "
            f"project) and NO BENEFIT. Delete them from the set (audit LAST-1)"
        )

    def test_the_deny_set_still_holds_every_LIVE_spawn_capable_module(self) -> None:
        """The over-correction pin: 'fixing' the false positive by emptying the set fails here.

        This list is written by hand, not derived from the code under test — a pin that asks
        the implementation what it denies and then asserts that it denies it is decoration.
        """
        missing = sorted(set(_LIVE_SPAWN_MODULE_NAMES) - _SPAWN_CAPABLE_MODULES)

        assert missing == [], (
            f"_SPAWN_CAPABLE_MODULES no longer denies {missing!r}. Each is a REAL, importable "
            f"module on 3.14 that can spawn a process — dropping one re-opens door 13 for it. "
            f"The LAST-1 fix removes exactly the three names that are not modules "
            f"({', '.join(_DEAD_MODULE_NAMES)}); it removes nothing else"
        )

    def test_the_CONTROL_the_image_runs_the_interpreter_this_pin_measured(self) -> None:
        """The premise both pins above rest on — pinned, not assumed.

        "``commands`` is dead" is a statement about a PYTHON VERSION, and the version that
        matters is the one the SHIPPED CODE runs, i.e. the image's. This test measured the dev
        interpreter. The two are the same by construction (``Containerfile``: ``FROM
        python:3.14-slim``; ``pyproject.toml``: ``requires-python = ">=3.14"``) — and if they
        ever diverge, the dead/live split must be RE-DERIVED against the image's interpreter
        before it can be trusted, so that divergence has to be loud.
        """
        containerfile = (_REPO_ROOT / "Containerfile").read_text(encoding="utf-8")
        match = re.search(r"^FROM python:(\d+)\.(\d+)", containerfile, re.MULTILINE)
        assert match is not None, "the Containerfile no longer declares a `FROM python:X.Y` base"
        image_version = (int(match.group(1)), int(match.group(2)))

        assert image_version == sys.version_info[:2], (
            f"the image runs Python {image_version[0]}.{image_version[1]} but this suite runs "
            f"{sys.version_info.major}.{sys.version_info.minor}. Which stdlib modules EXIST is "
            f"a property of the interpreter, and the spawn-capable deny set is now derived from "
            f"the one that ran the tests — so it is being measured against the wrong Python. "
            f"Re-derive the dead/live split on the IMAGE's interpreter before trusting the deny "
            f"set (audit LAST-1)"
        )


class TestTheFixCostsTheRealTreeNothing:
    """No collateral damage, at repo scale — with the anti-vacuity leg the other pins lack.

    ``required_binaries`` RAISES on the first refusal, so a clean derivation over the whole
    shipped tree IS the zero-false-positive proof — but only if the scan actually looked at
    something. A scan over zero modules also returns without refusing.
    """

    def test_the_real_tree_still_derives_git_with_zero_false_positives(self) -> None:
        shipped = _shipped_modules(_REPO_ROOT)

        assert len(shipped) > 50, (
            f"the scan saw only {len(shipped)} shipped modules — a derivation over (almost) "
            f"nothing cannot vouch for anything, and would make the assertion below vacuous"
        )
        assert required_binaries(_REPO_ROOT) == frozenset({"git"}), (
            f"the LAST-1 fix must not perturb the derived set for this repo: across all "
            f"{len(shipped)} shipped modules the only exec site is the seam's ``git``. A "
            f"refusal here would RAISE (a false positive on real code); a different set means "
            f"the deny/resolve boundary moved"
        )
