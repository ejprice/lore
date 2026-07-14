"""Derive the external binaries lore's SHIPPED code can execute (findings #125/#131).

The image must carry every binary the shipped packages can exec — today just ``git``,
which the ``capture_git_identity`` seam shells out to. It did NOT, and so the git-derived
fields (``lore_index()``'s watched-root branch, every snapshot's ``git_ref``) were a
silent ``None`` in production while every test on a git-having host stayed green.

The gate cannot be a list of forbidden losses (that set is unbounded and a name-list
always loses). It is the inverse: DERIVE the small, enumerable SAFE set from the source,
and let the deploy require exactly that. A new shell-out grows the required set BY ITSELF.

Coverage is a CHECKED variable, never a hope — and it is checked PER SITE, never per
module. Every call that reaches a process spawner is resolved into the set or raises
:class:`UnresolvedExecSiteError` naming ``file:line``. There is no third outcome. (There
was: the first cut keyed on RECEIVER NAMES — ``subprocess`` / ``os`` / ``asyncio`` — and
guarded coverage per MODULE, so ``import subprocess as sp`` and ``from os import system``
walked straight through it, and ONE readable call disarmed the check for a whole file. The
name-list losing again, inside the fix that cites the lesson.)

The spawner is therefore resolved through the module's own BINDINGS: whatever local name an
import or an assignment bound a spawner to, aliased or not, is what the scan follows. A
reference to a spawner the scan cannot follow to a literal ``argv[0]`` is a human verdict,
never a silent shrink of the set the deploy trusts.

An empty set is not, in itself, the danger — the CAUSE is:

* the scan found NO MODULES → :class:`ShelloutScanError` (a gate over nothing passes over
  everything);
* a module reaches a spawner in a form the scan cannot resolve →
  :class:`UnresolvedExecSiteError`;
* the shipped packages genuinely exec nothing → a legitimate ``frozenset()``, which the
  deploy reports in words.

This is the SOLE authority for the derivation (repo standing law, "ONE IMPLEMENTATION"):
both the repo's own contract (``loremaster/tests/test_shellout_allowlist.py``) and the
lore-deploy skill's artifact-gate probes call :func:`required_binaries` — neither keeps
a private copy of the scan.
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path
from typing import Any

# The spawn forms this scan understands, per spawner module. A call is an exec site when it
# reaches one of these — through ANY local name the module bound it to.
_SUBPROCESS_EXEC_CALLS = frozenset(
    {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
)
_OS_EXEC_CALLS = frozenset(
    {
        "system", "popen", "execv", "execve", "execvp", "execvpe", "execl", "execle",
        "execlp", "spawnv", "spawnve", "spawnvp", "spawnl", "spawnle", "spawnlp",
        "posix_spawn", "posix_spawnp",
    }
)
_ASYNCIO_EXEC_CALLS = frozenset({"create_subprocess_exec", "create_subprocess_shell"})

_SPAWNERS: dict[str, frozenset[str]] = {
    "subprocess": _SUBPROCESS_EXEC_CALLS,
    "os": _OS_EXEC_CALLS,
    "asyncio": _ASYNCIO_EXEC_CALLS,
}


class ShelloutScanError(RuntimeError):
    """The scan cannot vouch for the derived set — a human must rule, never a guess.

    The danger is the CAUSE, not the empty outcome. A scan over no modules, and a module
    whose spawn sites cannot be read, must never quietly become "this image needs nothing";
    both raise. Shipped packages that genuinely exec nothing are a legitimate empty answer.
    """


class UnresolvedExecSiteError(ShelloutScanError):
    """A shipped exec site whose ``argv[0]`` the scan cannot resolve. Names ``file:line``."""


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

    Deliberately not the whole member directory — a member's ``tests/`` tree is copied
    into the image but never runs there, and its shell-outs must not make the deploy
    demand binaries the image has no reason to carry.
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


class _SpawnScan:
    """One module's spawner BINDINGS, its exec sites, and every reference it cannot read.

    Two passes, and that is what makes coverage a per-SITE property. Pass 1 learns every
    local name that reaches a spawner (``import subprocess as sp``, ``from os import system
    as sh``, ``SPAWNER = subprocess.Popen``). Pass 2 resolves EVERY call made through one of
    them, and reports every OTHER reference to one as unreadable — so a single readable call
    can no longer vouch for its neighbours.
    """

    def __init__(self, tree: ast.Module, relative: Path) -> None:
        self._tree = tree
        self._relative = relative
        self._modules: dict[str, str] = {}  # local alias -> "subprocess" / "os" / "asyncio"
        self._callables: dict[str, str] = {}  # local alias -> the spawner module it came from
        self._consumed: set[int] = set()  # nodes a resolved call or a binding accounted for
        self._attribute_bases: set[int] = set()  # every ``x`` of an ``x.y`` in this module

    def binaries(self) -> set[str]:
        """The binaries this module execs — raising on any site or reference it cannot read."""
        self._learn_bindings()
        binaries: set[str] = set()
        for node in ast.walk(self._tree):
            if not isinstance(node, ast.Call) or self._spawner_of(node.func) is None:
                continue
            binary = _argv0(node)
            if binary is None:
                raise self._verdict(
                    node.lineno,
                    "cannot resolve argv[0] of this exec call. The image's required-binary "
                    "set is DERIVED from these sites, so an unreadable one is a human "
                    "verdict, never a silent skip: make argv[0] a literal, or install the "
                    "binary and teach this scan about it.",
                )
            self._consumed.add(id(node.func))
            binaries.add(binary)
        self._assert_every_spawner_reference_was_read()
        return binaries

    def _learn_bindings(self) -> None:
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                self._attribute_bases.add(id(node.value))
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in _SPAWNERS:
                        self._modules[alias.asname or alias.name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[0]
                if module in _SPAWNERS:
                    for alias in node.names:
                        if alias.name in _SPAWNERS[module]:
                            self._callables[alias.asname or alias.name] = module
        # Assignments are learned last: `SPAWNER = subprocess.Popen` needs the imports first.
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Assign):
                self._learn_assignment(node)

    def _learn_assignment(self, node: ast.Assign) -> None:
        """``SPAWNER = subprocess.Popen`` / ``launch = run``: a spawner under a new name."""
        module = self._spawner_of(node.value)
        if module is None:
            return
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._callables[target.id] = module
        self._consumed.add(id(node.value))

    def _spawner_of(self, node: ast.expr) -> str | None:
        """The spawner module this expression NAMES (whether or not it calls it)."""
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and (module := self._modules.get(node.value.id)) is not None
            and node.attr in _SPAWNERS[module]
        ):
            return module
        if isinstance(node, ast.Name):
            return self._callables.get(node.id)
        return None

    def _assert_every_spawner_reference_was_read(self) -> None:
        """Any OTHER way this module touches a spawner is a site the scan cannot read.

        ``functools.partial(subprocess.run, …)``, a ``SPAWNER`` handed to a caller,
        ``getattr(subprocess, name)`` — the scan cannot know what argv these launch, and an
        answer it cannot vouch for is a verdict, not a quietly smaller set.
        """
        for node in ast.walk(self._tree):
            if id(node) in self._consumed:
                continue
            if isinstance(node, ast.Attribute) and self._spawner_of(node) is not None:
                raise self._verdict(
                    node.lineno,
                    "this module NAMES a process spawner here without calling it with a "
                    "literal argv[0] — the scan cannot know what it launches, and an empty "
                    "answer here is how a required binary goes missing from the image "
                    "(findings #125/#131). A human must rule.",
                )
            if not isinstance(node, ast.Name):
                continue
            if node.id in self._callables:
                raise self._verdict(
                    node.lineno,
                    "this module REFERENCES a process spawner here without calling it with "
                    "a literal argv[0] — the scan cannot know what it launches. A human "
                    "must rule (findings #125/#131).",
                )
            if node.id in self._modules and id(node) not in self._attribute_bases:
                raise self._verdict(
                    node.lineno,
                    "this module hands the spawner module itself somewhere the scan cannot "
                    "follow — what it execs is unknowable from the source. A human must "
                    "rule (findings #125/#131).",
                )

    def _verdict(self, lineno: int, why: str) -> UnresolvedExecSiteError:
        return UnresolvedExecSiteError(f"{self._relative}:{lineno}: {why}")


def required_binaries(repo_root: Path) -> frozenset[str]:
    """Every external binary the shipped packages can exec — the image must carry each.

    Args:
        repo_root: The workspace root (the tree the image is built from).

    Returns:
        The derived safe set (e.g. ``frozenset({"git"})``). An empty set means the shipped
        packages exec nothing — a legitimate answer the scan has VOUCHED for, never a
        silently-lost one: both causes that would make it a lie raise instead.

    Raises:
        ShelloutScanError: ``repo_root`` declares no shipped packages at all (a scan
            over nothing yields an empty set, which is a gate that passes over anything).
        UnresolvedExecSiteError: A shipped exec site's ``argv[0]`` is not a literal, or a
            shipped module reaches a process spawner in a form the scan cannot follow to a
            literal. Either way the scan cannot vouch for the set and a human must rule —
            the deploy never proceeds on a required set it cannot trust. Names ``file:line``.
    """
    modules = _shipped_modules(repo_root)
    if not modules:
        raise ShelloutScanError(
            f"no shipped modules found under {repo_root} — its pyproject.toml declares no "
            f"[tool.uv.workspace] members (or their packages are missing). A scan over "
            f"nothing returns an EMPTY required set, which makes the deploy's binary gate "
            f"pass vacuously over a container that has nothing. Point the scan at the "
            f"workspace root the image is built from."
        )

    binaries: set[str] = set()
    for module in modules:
        relative = module.relative_to(repo_root)
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        binaries |= _SpawnScan(tree, relative).binaries()
    return frozenset(binaries)
