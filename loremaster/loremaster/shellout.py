"""Derive the external binaries lore's SHIPPED code can execute (findings #125/#131).

The image must carry every binary the shipped packages can exec — today just ``git``,
which the ``capture_git_identity`` seam shells out to. It did NOT, and so the git-derived
fields (``lore_index()``'s watched-root branch, every snapshot's ``git_ref``) were a
silent ``None`` in production while every test on a git-having host stayed green.

The gate cannot be a list of forbidden losses (that set is unbounded and a name-list
always loses). It is the inverse: DERIVE the small, enumerable SAFE set from the source,
and let the deploy require exactly that. A new shell-out grows the required set BY ITSELF.

Coverage is a CHECKED variable, never a hope: an exec site whose ``argv[0]`` is not a
literal, and a shipped module that can spawn a process but shows no resolvable exec site,
both raise :class:`UnresolvedExecSiteError` — a human verdict — rather than silently
shrinking the set the deploy trusts.

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

# The spawn forms this scan understands, per module. Anything a shipped module does that
# LOOKS like spawning but yields no resolved site raises instead (see ``_can_spawn``).
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


class ShelloutScanError(RuntimeError):
    """The scan cannot vouch for the derived set — a human must rule, never a guess.

    An EMPTY answer is the dangerous one: it makes the deploy's binary gate pass
    vacuously ("container binaries OK ()") over a container missing everything.
    """


class UnresolvedExecSiteError(ShelloutScanError):
    """A shipped exec site whose ``argv[0]`` the scan cannot resolve."""


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


def _exec_receiver(node: ast.Call) -> str | None:
    """The spawn family this call belongs to (``subprocess`` / ``os`` / ``asyncio``)."""
    func = node.func
    if isinstance(func, ast.Await):  # pragma: no cover - defensive
        return None
    if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name):
        return None
    receiver, attribute = func.value.id, func.attr
    if receiver == "subprocess" and attribute in _SUBPROCESS_EXEC_CALLS:
        return receiver
    if receiver == "os" and attribute in _OS_EXEC_CALLS:
        return receiver
    if receiver == "asyncio" and attribute in _ASYNCIO_EXEC_CALLS:
        return receiver
    return None


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


def _can_spawn(tree: ast.Module) -> bool:
    """Does this module reach for a process spawner at all (however it then uses it)?"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == "subprocess" for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "subprocess":
                return True
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            receiver, attribute = node.value.id, node.attr
            if receiver == "os" and attribute in _OS_EXEC_CALLS:
                return True
            if receiver == "asyncio" and attribute in _ASYNCIO_EXEC_CALLS:
                return True
    return False


def required_binaries(repo_root: Path) -> frozenset[str]:
    """Every external binary the shipped packages can exec — the image must carry each.

    Args:
        repo_root: The workspace root (the tree the image is built from).

    Returns:
        The derived safe set (e.g. ``frozenset({"git"})``).

    Raises:
        ShelloutScanError: ``repo_root`` declares no shipped packages at all (a scan
            over nothing yields an empty set, which is a gate that passes over anything).
        UnresolvedExecSiteError: A shipped exec site's ``argv[0]`` is not a literal, or a
            shipped module can spawn a process but shows no resolvable exec site. Either
            way the scan cannot vouch for the set, and a human must rule — the deploy
            never proceeds on a required set it cannot trust.
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
        resolved_sites = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _exec_receiver(node) is None:
                continue
            binary = _argv0(node)
            if binary is None:
                raise UnresolvedExecSiteError(
                    f"{relative}:{node.lineno}: cannot resolve argv[0] of this exec call. "
                    f"The image's required-binary set is DERIVED from these sites, so an "
                    f"unreadable one is a human verdict, never a silent skip: make argv[0] "
                    f"a literal, or install the binary and teach this scan about it."
                )
            resolved_sites += 1
            binaries.add(binary)
        if resolved_sites == 0 and _can_spawn(tree):
            raise UnresolvedExecSiteError(
                f"{relative}: this shipped module can spawn a process but shows no "
                f"resolvable exec site — the scan does not understand what it launches, "
                f"and an empty answer here is how a required binary goes missing from the "
                f"image (findings #125/#131). A human must rule."
            )
    return frozenset(binaries)
