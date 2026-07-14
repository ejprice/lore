"""Derive the external binaries lore's SHIPPED code can execute (findings #125/#131).

The image must carry every binary the shipped packages can exec — today just ``git``, which
the ``capture_git_identity`` seam shells out to. It did NOT, and so the git-derived fields
(``lore_index()``'s watched-root branch, every snapshot's ``git_ref``) were a silent ``None``
in production for three months while every test on a git-having host stayed green.

ONE SANCTIONED EXEC SEAM
------------------------
No shipped module may reach a process spawner AT ALL, except an explicit allowlist —
:data:`SANCTIONED_EXEC_MODULES`, which today holds exactly one file:
``loremaster/loremaster/index/snapshots.py``.

This is the third design for this gate. The first keyed on RECEIVER NAMES
(``subprocess``/``os``/``asyncio``) and was defeated by ``import subprocess as sp`` and
``from os import system``. The second followed each module's BINDINGS and was defeated by
``self._runner = subprocess.run``, by ``import os.path`` + ``os.system(...)``, and by
``from subprocess import *``. Both lost the same way, and the way they lost is the point:
**a scan whose job is to RESOLVE arbitrary modules must model every route to a spawner, and
that set is unbounded.** A route it does not model shrinks the required set SILENTLY — which
is #131, exactly.

So the posture is inverted, per this repo's standing law (*"the forbidden set is unbounded;
the SAFE set is small and enumerable — allowlist the safe"*):

* **The DENY side over-approximates and fails LOUD.** Outside the seam this scan does not try
  to recognise HOW a module reaches a spawner — only that it MIGHT. Any doubt is a refusal
  naming ``file:line``. A false positive is CHEAP and CORRECT: a human either sanctions the
  module (a visible, reviewed edit to the allowlist) or routes it through the seam. **Erring
  loud is the design.** It is what ends the shape game — an evading shape in a non-sanctioned
  module still trips a detector that is not trying to be clever.
* **The RESOLVE side is precise, and lives ONLY inside the seam.** We cannot demand a
  canonical, readable form of the whole codebase. We can demand it of ONE file. Inside it,
  ``argv[0]`` resolves to a literal or the scan fails loud.
* **The allowlist is a CHECKED artifact.** It cannot be grown from inside a module (no
  pragma, no marker), a stale entry raises, and a sanctioned module that execs nothing raises
  — an exemption must be NEEDED. Sanction a file and its binary enters the derived set,
  whereupon the contract demands the image install it. Nobody has to remember anything.

An empty set is not, in itself, the danger — the CAUSE is:

* the scan found NO MODULES → :class:`ShelloutScanError` (a gate over nothing passes over
  everything);
* a non-sanctioned module reaches a spawner, or a sanctioned one is unreadable →
  :class:`UnresolvedExecSiteError`;
* the shipped packages genuinely exec nothing → a legitimate ``frozenset()``, which the
  deploy reports in words.

KNOWN BOUND (ledgered, not fixed): a THIRD-PARTY dependency that spawns on our behalf
(``plumbum``, ``pexpect``, ``GitPython``) is invisible to an AST scan of our own source.
Closing it means scanning site-packages, which would make the deploy demand every binary
every dependency can reach. We ship no such dependency today.

This is the SOLE authority for the derivation (repo standing law, "ONE IMPLEMENTATION"):
both the repo's own contract (``loremaster/tests/test_shellout_allowlist.py``) and the
lore-deploy skill's artifact-gate probes call :func:`required_binaries` — neither keeps a
private copy of the scan.
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# THE SAFE SET. Every other shipped module is denied a process spawner outright.
#
# Growing this is the most security-relevant edit anyone can make to this instrument, so it is
# a deliberate RED in the contract: a human must come here, read the architecture above,
# confirm the new seam's argv[0] resolves, and confirm the binary is INSTALLED IN THE IMAGE.
# --------------------------------------------------------------------------- #
SANCTIONED_EXEC_MODULES: frozenset[str] = frozenset(
    {"loremaster/loremaster/index/snapshots.py"}
)

# --------------------------------------------------------------------------- #
# THE DENY SIDE — receiver-blind, binding-blind, deliberately coarse.
#
# Note what these sets are and are NOT. They are NOT an enumeration of the ways to REACH a
# spawner (that set is unbounded — it is what beat v1 and v2). They are the CLOSED, DOCUMENTED
# stdlib surfaces through which a process spawn can happen at all: the spawn-capable modules,
# the os/asyncio spawn APIs, and the import machinery. A future author cannot extend them by
# inventing a new alias — only CPython can, by growing its own API.
# --------------------------------------------------------------------------- #
_SPAWN_CAPABLE_MODULES = frozenset(
    {
        "subprocess", "pty", "multiprocessing", "posix", "_posixsubprocess", "popen2",
        "commands", "imp",
        # FFI reaches libc's own system(3)/exec(3) without touching a Python spawn API.
        "ctypes",
        # webbrowser.open() launches a browser BINARY.
        "webbrowser",
    }
)

# ``os``' process-spawn API — the closed, documented set. ``os`` itself is imported all over
# shipped code for ``os.path`` / ``os.environ``, so it cannot be denied wholesale; its SPAWN
# surface can be, and that surface is bounded in a way "every way to bind a name" never is.
_OS_SPAWN_API = frozenset(
    {
        "system", "popen", "execl", "execle", "execlp", "execlpe", "execv", "execve",
        "execvp", "execvpe", "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve",
        "spawnvp", "spawnvpe", "posix_spawn", "posix_spawnp", "fork", "forkpty", "startfile",
    }
)
_ASYNCIO_SPAWN_API = frozenset({"create_subprocess_exec", "create_subprocess_shell"})
_SPAWN_PRIMITIVES = _OS_SPAWN_API | _ASYNCIO_SPAWN_API

# The import machinery: the one way to obtain a spawn-capable module without an import
# statement. (``importlib.resources`` / ``importlib.metadata`` are NOT machinery and ARE used
# by shipped code — only the machinery names below are denied.)
_DYNAMIC_REACH = frozenset(
    {"__import__", "import_module", "load_module", "exec_module", "eval", "exec"}
)

# The doors that hand out a module's namespace WHOLESALE, naming no primitive at all:
# ``getattr(os, "sys" + "tem")``, ``vars(os)["system"]``, ``os.__dict__[...]``,
# ``sys.modules["subprocess"]``. Receiver-blindness cannot see these — there is no spawn name
# to see — so they are denied on any name the module IMPORTED.
_MODULE_NAMESPACE_DOORS = frozenset({"__dict__", "modules"})
_NAMESPACE_BUILTINS = frozenset({"getattr", "setattr", "delattr", "vars"})

# --------------------------------------------------------------------------- #
# THE RESOLVE SIDE — the spawn CALLS whose argv[0] the seam must make readable.
# --------------------------------------------------------------------------- #
_SUBPROCESS_EXEC_CALLS = frozenset(
    {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
)
_SPAWN_CALLS = _SUBPROCESS_EXEC_CALLS | _SPAWN_PRIMITIVES

# The modules a sanctioned seam may spawn THROUGH, and the only form it may import them in.
_SEAM_SPAWNER_MODULES = _SPAWN_CAPABLE_MODULES | {"os", "asyncio"}


class ShelloutScanError(RuntimeError):
    """The scan cannot vouch for the derived set — a human must rule, never a guess.

    The danger is the CAUSE, not the empty outcome. A scan over no modules, a stale allowlist
    entry, and a sanctioned module that execs nothing must never quietly become "this image
    needs nothing"; all raise. Shipped packages that genuinely exec nothing are a legitimate
    empty answer.
    """


class UnresolvedExecSiteError(ShelloutScanError):
    """A shipped module reached a process spawner the scan will not vouch for.

    Outside the sanctioned seam that means it reached one AT ALL. Inside it, that means its
    ``argv[0]`` could not be read. Either way: names ``file:line``, and a human rules.
    """


def _workspace_members(repo_root: Path) -> list[str]:
    """The uv-workspace members: exactly the packages the image installs."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return []
    data: dict[str, Any] = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    tool = data.get("tool", {})
    workspace = tool.get("uv", {}).get("workspace", {}) if isinstance(tool, dict) else {}
    members = workspace.get("members", []) if isinstance(workspace, dict) else []
    return [str(member) for member in members]


def _shipped_modules(repo_root: Path) -> list[Path]:
    """Every module that RUNS in the image: each member's installed package.

    Deliberately not the whole member directory — a member's ``tests/`` tree is copied into
    the image but never runs there. Its shell-outs must not make the deploy demand binaries
    the image has no reason to carry, and (just as important) the deny side must not force
    every test file that shells out to be sanctioned: an instrument that noisy gets deleted.
    """
    modules: list[Path] = []
    for member in _workspace_members(repo_root):
        package = repo_root / member / member
        if package.is_dir():
            modules.extend(sorted(package.rglob("*.py")))
    return modules


def _argv0(node: ast.Call) -> str | None:
    """The literal binary this call site execs, or ``None`` when it cannot be resolved."""
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        parts = first.value.split()
        return parts[0] if parts else None
    if isinstance(first, ast.List | ast.Tuple) and first.elts:
        head = first.elts[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, str):
            return head.value
    return None


def _verdict(relative: str, lineno: int, why: str) -> UnresolvedExecSiteError:
    return UnresolvedExecSiteError(f"{relative}:{lineno}: {why} (findings #125/#131)")


def _deny_identifier(identifier: str, relative: str, lineno: int) -> None:
    """Refuse a bare name or attribute that IS a spawn / import-machinery primitive.

    Receiver-blind on purpose: ``anything.system(...)`` is refused on the strength of
    ``system`` alone. v1 keyed on the receiver names, and the repo's instrument table records
    the result — *"a gate keyed on 2 receiver names, defeated by six other doors."*
    """
    if identifier in _SPAWN_PRIMITIVES:
        raise _verdict(
            relative, lineno,
            f"names the process-spawn primitive {identifier!r}. The scan deliberately does "
            f"not look at WHAT you call it on — the spawn API is a closed set; the ways to "
            f"bind a name to it are not",
        )
    if identifier in _DYNAMIC_REACH:
        raise _verdict(
            relative, lineno,
            f"names the import-machinery primitive {identifier!r}, which can obtain a "
            f"process-spawn module without an import statement",
        )


def _deny_import(node: ast.Import, relative: str, imported: set[str]) -> None:
    """``import subprocess`` / ``import subprocess as sp`` / ``import asyncio.subprocess``."""
    for alias in node.names:
        if set(alias.name.split(".")) & _SPAWN_CAPABLE_MODULES:
            raise _verdict(
                relative, node.lineno,
                f"imports the process-spawn module {alias.name!r}. Only a SANCTIONED exec "
                f"seam may reach a spawner: route this through one, or add this file to "
                f"SANCTIONED_EXEC_MODULES and install its binary in the image",
            )
        imported.add((alias.asname or alias.name).split(".")[0])


def _deny_import_from(node: ast.ImportFrom, relative: str, imported: set[str]) -> None:
    """``from subprocess import run`` / ``from os import system`` / ``from os import *``."""
    module = node.module or ""
    if set(module.split(".")) & _SPAWN_CAPABLE_MODULES:
        raise _verdict(
            relative, node.lineno, f"imports from the process-spawn module {module!r}"
        )
    for alias in node.names:
        if alias.name == "*":
            raise _verdict(
                relative, node.lineno,
                f"star-imports from {module!r} — a star-import can smuggle any name, a "
                f"spawner included, so the scan cannot vouch for what this module can reach",
            )
        if alias.name in _SPAWN_CAPABLE_MODULES or alias.name in _SPAWN_PRIMITIVES:
            raise _verdict(
                relative, node.lineno,
                f"imports the process-spawn name {alias.name!r} from {module!r}",
            )
        if alias.name in _DYNAMIC_REACH:
            raise _verdict(
                relative, node.lineno,
                f"imports the import-machinery primitive {alias.name!r}, which can obtain a "
                f"spawner without an import statement",
            )
        imported.add(alias.asname or alias.name)


def _deny_namespace_doors(tree: ast.Module, relative: str, imported: set[str]) -> None:
    """The doors that hand out a module's namespace without naming a primitive at all."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in imported
            and node.attr in _MODULE_NAMESPACE_DOORS
        ):
            raise _verdict(
                relative, node.lineno,
                f"reaches into the NAMESPACE of the imported module {node.value.id!r} via "
                f"{node.attr!r} — which can hand out a spawner without ever naming one",
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _NAMESPACE_BUILTINS
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in imported
        ):
            raise _verdict(
                relative, node.lineno,
                f"reaches into the NAMESPACE of the imported module {node.args[0].id!r} via "
                f"{node.func.id}() — which can hand out a spawner without ever naming one",
            )


def _deny_spawn_capability(tree: ast.Module, relative: str) -> None:
    """A module outside the seam may not reach a process spawner. Any doubt is a refusal.

    Deliberately blind to the RECEIVER and to the CALL SHAPE: the verdict is a function of the
    CAPABILITY reaching this module, never of what it then does with it. That is what makes
    the shape game unwinnable — there is nothing here for a clever shape to evade.

    Args:
        tree: The module's parsed AST.
        relative: Its repo-relative POSIX path, for the verdict message.

    Raises:
        UnresolvedExecSiteError: The module can reach a process spawner. Names ``file:line``.
    """
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            _deny_import(node, relative, imported)
        elif isinstance(node, ast.ImportFrom):
            _deny_import_from(node, relative, imported)
        elif isinstance(node, ast.Attribute):
            _deny_identifier(node.attr, relative, node.lineno)
        elif isinstance(node, ast.Name):
            _deny_identifier(node.id, relative, node.lineno)
    _deny_namespace_doors(tree, relative, imported)


def _resolve_sanctioned(tree: ast.Module, relative: str) -> set[str]:
    """The binaries the SANCTIONED seam execs — demanding a canonical, readable form.

    We cannot demand this of the whole codebase. We can demand it of one reviewed file: import
    the spawner plainly, call it directly, and make ``argv[0]`` a literal. Anything else is a
    refusal — a spawner stashed on ``self``, a module constant holding ``Popen``, a
    ``functools.partial``, an alias, a from-import. (This is where audit residual RA1 dies by
    construction: there is no assignment-learning here, so there is nothing to suppress the
    fail-loud reference check.)

    Args:
        tree: The seam's parsed AST.
        relative: Its repo-relative POSIX path.

    Returns:
        The literal ``argv[0]`` of every exec site in the seam.

    Raises:
        UnresolvedExecSiteError: The seam reaches a spawner in a form the scan cannot read.
    """
    spawner_modules = _seam_spawner_modules(tree, relative)
    binaries = _seam_binaries(tree, relative, spawner_modules)
    _deny_loose_spawner_reference(tree, relative, spawner_modules)
    return binaries


def _seam_spawner_modules(tree: ast.Module, relative: str) -> set[str]:
    """The spawner modules the seam imported — demanding the plain, unaliased form."""
    spawner_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in _SEAM_SPAWNER_MODULES:
                    continue
                if alias.asname is not None or "." in alias.name:
                    raise _verdict(
                        relative, node.lineno,
                        f"the sanctioned exec seam must import {alias.name!r} PLAINLY (no "
                        f"alias, no dotted form) — the seam is the one file whose exec sites "
                        f"the deploy trusts to be complete, so its form is not negotiable",
                    )
                spawner_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = {alias.name for alias in node.names}
            if (set(module.split(".")) & _SEAM_SPAWNER_MODULES) and (
                names & (_SPAWN_CALLS | _SPAWN_CAPABLE_MODULES | {"*"})
            ):
                raise _verdict(
                    relative, node.lineno,
                    f"the sanctioned exec seam must not from-import a spawner from {module!r} "
                    f"— import the module plainly and call it directly, so every exec site "
                    f"reads as one",
                )
    return spawner_modules


def _seam_binaries(tree: ast.Module, relative: str, spawner_modules: set[str]) -> set[str]:
    """Every ``<spawner>.<exec_call>(...)`` in the seam, resolved to its literal ``argv[0]``."""
    calls_by_func = {
        id(node.func): node for node in ast.walk(tree) if isinstance(node, ast.Call)
    }
    binaries: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if not (isinstance(node.value, ast.Name) and node.value.id in spawner_modules):
            continue
        if node.attr not in _SPAWN_CALLS:
            continue  # subprocess.PIPE, subprocess.SubprocessError — not a spawn.
        call = calls_by_func.get(id(node))
        if call is None:
            raise _verdict(
                relative, node.lineno,
                f"NAMES the spawner {node.value.id}.{node.attr} without calling it here — the "
                f"scan cannot know what argv it will eventually launch. Call it directly, "
                f"with a literal argv[0]",
            )
        binary = _argv0(call)
        if binary is None:
            raise _verdict(
                relative, node.lineno,
                "cannot resolve argv[0] of this exec call. The image's required-binary set is "
                "DERIVED from these sites, so an unreadable one is a human verdict, never a "
                "silent skip: make argv[0] a literal",
            )
        binaries.add(binary)
    return binaries


def _deny_loose_spawner_reference(
    tree: ast.Module, relative: str, spawner_modules: set[str]
) -> None:
    """The seam may not hand the spawner MODULE itself anywhere the scan cannot follow."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name) or node.id not in spawner_modules:
            continue
        if node.id not in _SPAWN_CAPABLE_MODULES:
            continue  # a bare ``os`` / ``asyncio`` is ordinary; a bare ``subprocess`` is not.
        if any(
            isinstance(parent, ast.Attribute) and parent.value is node
            for parent in ast.walk(tree)
        ):
            continue
        raise _verdict(
            relative, node.lineno,
            f"hands the spawner module {node.id!r} somewhere the scan cannot follow — what it "
            f"execs is unknowable from the source",
        )


def required_binaries(
    repo_root: Path, *, sanctioned: frozenset[str] = SANCTIONED_EXEC_MODULES
) -> frozenset[str]:
    """Every external binary the shipped packages can exec — the image must carry each.

    Args:
        repo_root: The workspace root (the tree the image is built from).
        sanctioned: The repo-relative POSIX paths allowed to reach a process spawner. Defaults
            to :data:`SANCTIONED_EXEC_MODULES`, which is what the deploy uses — the keyword
            exists so the contract's synthetic workspaces can declare their own seam.

    Returns:
        The derived safe set (e.g. ``frozenset({"git"})``). An empty set means the shipped
        packages exec nothing — a legitimate answer the scan has VOUCHED for, never a silently
        lost one: every cause that would make it a lie raises instead.

    Raises:
        ShelloutScanError: ``repo_root`` declares no shipped packages (a scan over nothing
            yields an empty set, which is a gate that passes over anything); or ``sanctioned``
            names a module that does not exist (a stale exemption is a hole waiting for a file
            to be created at that path); or a sanctioned module execs nothing (an exemption
            must be NEEDED — deny-by-default, evidence-backed).
        UnresolvedExecSiteError: A module outside the seam can reach a process spawner, or a
            sanctioned module's ``argv[0]`` is not readable. Either way the scan cannot vouch
            for the set and a human must rule. Names ``file:line``.
    """
    modules = _shipped_modules(repo_root)
    if not modules:
        raise ShelloutScanError(
            f"no shipped modules found under {repo_root} — its pyproject.toml declares no "
            f"[tool.uv.workspace] members (or their packages are missing). A scan over nothing "
            f"returns an EMPTY required set, which makes the deploy's binary gate pass "
            f"vacuously over a container that has nothing. Point the scan at the workspace "
            f"root the image is built from."
        )

    binaries: set[str] = set()
    seen: set[str] = set()
    for module in modules:
        relative = module.relative_to(repo_root).as_posix()
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        if relative not in sanctioned:
            _deny_spawn_capability(tree, relative)
            continue
        seen.add(relative)
        found = _resolve_sanctioned(tree, relative)
        if not found:
            raise ShelloutScanError(
                f"{relative}: SANCTIONED as an exec seam, but it execs NOTHING. An exemption "
                f"nobody needs is an open door for the next shell-out to be written behind, "
                f"unreviewed — remove it from SANCTIONED_EXEC_MODULES."
            )
        binaries |= found

    if stale := sorted(sanctioned - seen):
        raise ShelloutScanError(
            f"SANCTIONED_EXEC_MODULES names module(s) that do not exist under {repo_root}: "
            f"{stale}. A stale exemption is a hole waiting for a file to be created at that "
            f"path — delete the entry, or fix the path."
        )
    return frozenset(binaries)
